// SPDX-License-Identifier: GPL-2.0-or-later
// Video-only bridge. No APK bytes, URLs, credentials or UI screenshots are read.
#import <UIKit/UIKit.h>
#import <objc/message.h>
#import <AVKit/AVKit.h>
#import <AVFoundation/AVFoundation.h>
#import <CoreMedia/CoreMedia.h>
#import <CoreVideo/CoreVideo.h>
#import <AudioToolbox/AudioToolbox.h>
#include <pthread.h>
#include <stdatomic.h>
#include "frame_mailbox.h"

typedef void (*PlaybackControl)(int background, int playing);
static pthread_mutex_t mailboxLock = PTHREAD_MUTEX_INITIALIZER;
static struct HuskFrameMailbox mailbox;
static PlaybackControl playbackControl;
static AudioQueueRef pendingAudioQueue;
static _Atomic unsigned policy; // bit 0: owns playback; bit 1: picture paused; bit 2: consume live while muted
static _Atomic BOOL hostBackground;

@interface HuskVideoPiP : NSObject <AVPictureInPictureControllerDelegate, AVPictureInPictureSampleBufferPlaybackDelegate, UIGestureRecognizerDelegate>
@property AVSampleBufferDisplayLayer *video;
@property AVPictureInPictureController *pip;
@property UIButton *button;
@property UITapGestureRecognizer *screenTap;
@property CFTimeInterval controlsVisibleUntil;
@property UIView *panel;
@property UIButton *back;
@property NSTimer *timer;
@property BOOL wantsPiP;
@property BOOL startRequested;
@property BOOL paused;
@property CFTimeInterval lastFrame;
@property CFTimeInterval startDeadline;
@property CFTimeInterval nextStartAttempt;
@property NSUInteger submittedVideoFrames;
@property NSUInteger startAttempts;
@property CMTimebaseRef timebase;
@property AudioQueueRef audioQueue;
@property BOOL audioMuted;
@property Float32 savedVolume;
- (void)consume:(CVPixelBufferRef)pixel;
- (void)setLiveAudioMuted:(BOOL)muted;
- (void)tick;
- (void)setupPiPController;
@end
extern void husk_appclip_install(void);
static HuskVideoPiP *shared;
__attribute__((constructor)) static void husk_video_pip_boot(void) {
    dispatch_async(dispatch_get_main_queue(), ^{
        husk_appclip_install();
        if (!shared) shared = [HuskVideoPiP new];
        NSLog(@"HuskVideoPiP: module loaded; native control initialized");
    });
}

static UIView *hostView(void) {
    // Put controls on the existing window, above presented player controllers.
    // A root controller view can be hidden underneath SwiftUI fullScreenCover.
    // Never create another UIWindow or capture the host window.
    for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
        if (![scene isKindOfClass:UIWindowScene.class] || scene.activationState != UISceneActivationStateForegroundActive) continue;
        for (UIWindow *window in ((UIWindowScene *)scene).windows)
            if (window.isKeyWindow && !window.hidden && window.rootViewController) return window;
    }
    return nil;
}
static void applyPlayback(int command) {
    PlaybackControl cb;
    pthread_mutex_lock(&mailboxLock); cb = playbackControl; pthread_mutex_unlock(&mailboxLock);
    if (cb) cb(atomic_load(&hostBackground), command);
}
static void drain(void) {
    CVPixelBufferRef pixel; AudioQueueRef queue;
    pthread_mutex_lock(&mailboxLock);
    pixel = husk_frame_take(&mailbox); queue = pendingAudioQueue;
    pthread_mutex_unlock(&mailboxLock);
    if (!pixel) return;
    @autoreleasepool {
        if (!shared) shared = [HuskVideoPiP new];
        if (shared.audioQueue != queue) {
            [shared setLiveAudioMuted:NO];
            shared.audioQueue = queue;
            if (shared.paused) [shared setLiveAudioMuted:YES];
        }
        [shared consume:pixel];
    }
    CVPixelBufferRelease(pixel);
}
__attribute__((visibility("default"))) void husk_video_pip_enqueue(CVPixelBufferRef pixel, int64_t pts, PlaybackControl cb, AudioQueueRef queue) {
    (void)pts;
    if (!pixel) return;
    CVPixelBufferRetain(pixel);
    pthread_mutex_lock(&mailboxLock);
    int schedule;
    CVPixelBufferRef old = husk_frame_offer(&mailbox, pixel, &schedule);
    playbackControl = cb; pendingAudioQueue = queue;
    pthread_mutex_unlock(&mailboxLock);
    if (old) CVPixelBufferRelease(old);
    if (schedule) dispatch_async(dispatch_get_main_queue(), ^{ drain(); });
}
__attribute__((visibility("default"))) unsigned husk_video_pip_policy(int background) {
    atomic_store(&hostBackground, background != 0);
    return atomic_load(&policy);
}

@implementation HuskVideoPiP
- (instancetype)init {
    if (!(self = [super init])) return nil;
    _video = [AVSampleBufferDisplayLayer new];
    _video.videoGravity = AVLayerVideoGravityResizeAspect;
    CMTimebaseRef timebase = NULL;
    if (CMTimebaseCreateWithSourceClock(kCFAllocatorDefault, CMClockGetHostTimeClock(), &timebase) == noErr) {
        _timebase = timebase;
        CMTimebaseSetTime(timebase, kCMTimeZero);
        CMTimebaseSetRate(timebase, 1.0);
        _video.controlTimebase = timebase;
    }
    [self setupPiPController];
    _button = [UIButton buttonWithType:UIButtonTypeSystem];
    [_button setImage:[UIImage systemImageNamed:@"pip.enter"] forState:UIControlStateNormal];
    _button.backgroundColor = [UIColor colorWithWhite:0 alpha:0.75];
    _button.tintColor = UIColor.whiteColor; _button.layer.cornerRadius = 22;
    _button.accessibilityLabel = @"Show livestream in Picture in Picture";
    [_button addTarget:self action:@selector(start) forControlEvents:UIControlEventTouchUpInside];
    [_button addTarget:self action:@selector(buttonPressed:) forControlEvents:UIControlEventTouchDown];
    _screenTap = [[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(screenTapped:)];
    _screenTap.cancelsTouchesInView = NO;
    _screenTap.delaysTouchesBegan = NO;
    _screenTap.delaysTouchesEnded = NO;
    _screenTap.delegate = self;
    _timer = [NSTimer scheduledTimerWithTimeInterval:0.25 target:self selector:@selector(tick) userInfo:nil repeats:YES];
    return self;
}
- (void)setupPiPController {
    // One controller per display layer for its entire lifetime; AVKit has async callbacks.
    if (self.pip) return;
    if (![AVPictureInPictureController isPictureInPictureSupported]) { self.pip = nil; return; }
    AVPictureInPictureControllerContentSource *source = [[AVPictureInPictureControllerContentSource alloc] initWithSampleBufferDisplayLayer:self.video playbackDelegate:self];
    self.pip = [[AVPictureInPictureController alloc] initWithContentSource:source];
    self.pip.delegate = self;
    self.pip.requiresLinearPlayback = YES;
    self.pip.canStartPictureInPictureAutomaticallyFromInline = NO;
}
- (void)dealloc { if (_timebase) CFRelease(_timebase); }
- (void)consume:(CVPixelBufferRef)pixel {
    CFTimeInterval now = CACurrentMediaTime();
    if (self.lastFrame <= 0 || now - self.lastFrame >= 3.0) self.controlsVisibleUntil = now + 3.0;
    self.lastFrame = now;
    [self tick];
    // Keep the PiP layer idle unless explicitly requested by the user.
    if (self.paused || (!self.panel && !self.pip.isPictureInPictureActive)) return;
    if (self.video.status == AVQueuedSampleBufferRenderingStatusFailed) [self.video flush];
    if (!self.video.readyForMoreMediaData) return;
    CMVideoFormatDescriptionRef format = NULL;
    CMSampleBufferRef sample = NULL;
    if (CMVideoFormatDescriptionCreateForImageBuffer(kCFAllocatorDefault, pixel, &format) != noErr) return;
    CMSampleTimingInfo timing = { kCMTimeInvalid, self.timebase ? CMTimebaseGetTime(self.timebase) : CMClockGetTime(CMClockGetHostTimeClock()), kCMTimeInvalid };
    OSStatus result = CMSampleBufferCreateReadyWithImageBuffer(kCFAllocatorDefault, pixel, format, &timing, &sample);
    if (result == noErr && sample) {
        CFArrayRef attachments = CMSampleBufferGetSampleAttachmentsArray(sample, YES);
        if (attachments && CFArrayGetCount(attachments)) CFDictionarySetValue((CFMutableDictionaryRef)CFArrayGetValueAtIndex(attachments, 0), kCMSampleAttachmentKey_DisplayImmediately, kCFBooleanTrue);
        [self.video enqueueSampleBuffer:sample];
        self.submittedVideoFrames++;
        CFRelease(sample);
    }
    CFRelease(format);
}
- (void)tick {
    UIView *host = hostView();
    BOOL recent = self.lastFrame > 0 && CACurrentMediaTime() - self.lastFrame < 3.0;
    if (host && self.button.superview != host) [host addSubview:self.button];
    if (host && self.screenTap.view != host) {
        [self.screenTap.view removeGestureRecognizer:self.screenTap];
        [host addGestureRecognizer:self.screenTap];
    }
    if (self.button.isTracking || self.button.isHighlighted) self.controlsVisibleUntil = CACurrentMediaTime() + 3.0;
    self.button.hidden = !host || !self.pip || !recent || self.panel || self.pip.isPictureInPictureActive || CACurrentMediaTime() >= self.controlsVisibleUntil;
    [self.button setTitle:nil forState:UIControlStateNormal];
    self.button.accessibilityLabel = @"Show livestream in Picture in Picture";
    if (host) {
        UIEdgeInsets inset = host.safeAreaInsets;
        self.button.frame = CGRectMake(MAX(inset.left + 8, host.bounds.size.width - inset.right - 88), inset.top + 8, 44, 44);
        [host bringSubviewToFront:self.button];
        if (self.panel) {
            self.panel.frame = host.bounds; self.video.frame = self.panel.bounds;
            self.back.frame = CGRectMake(inset.left + 12, inset.top + 12, 92, 44);
        }
    }
    CFTimeInterval now = CACurrentMediaTime();
    if ((self.wantsPiP || self.startRequested) && now >= self.startDeadline) {
        NSLog(@"HuskVideoPiP: startup timed out after %lu attempts", (unsigned long)self.startAttempts);
        [self finish];
        return;
    }
    BOOL displayed = self.video.status == AVQueuedSampleBufferRenderingStatusRendering;
    SEL readySelector = NSSelectorFromString(@"isReadyForDisplay");
    if ([self.video respondsToSelector:readySelector]) displayed = displayed && ((BOOL (*)(id, SEL))objc_msgSend)(self.video, readySelector);
    BOOL sourceReady = self.panel.window != nil && self.video.superlayer != nil && self.submittedVideoFrames >= 2 && displayed;
    if (self.wantsPiP && sourceReady && now >= self.nextStartAttempt && self.pip.isPictureInPicturePossible) {
        self.wantsPiP = NO; self.startRequested = YES; self.startAttempts++;
        NSLog(@"HuskVideoPiP: starting attempt %lu with %lu displayed-source frames", (unsigned long)self.startAttempts, (unsigned long)self.submittedVideoFrames);
        [self.pip startPictureInPicture];
    }
}
// Observe screen taps without cancelling the Android player's own touch handling.
- (void)buttonPressed:(UIButton *)sender {
    self.controlsVisibleUntil = CACurrentMediaTime() + 3.0;
}
- (void)screenTapped:(UITapGestureRecognizer *)recognizer {
    if (recognizer.state != UIGestureRecognizerStateRecognized || self.panel || self.pip.isPictureInPictureActive) return;
    if (self.lastFrame > 0 && CACurrentMediaTime() - self.lastFrame < 3.0) {
        self.controlsVisibleUntil = CACurrentMediaTime() + 3.0;
        [self tick];
    }
}
- (BOOL)gestureRecognizer:(UIGestureRecognizer *)recognizer shouldRecognizeSimultaneouslyWithGestureRecognizer:(UIGestureRecognizer *)other { return YES; }
- (BOOL)gestureRecognizer:(UIGestureRecognizer *)recognizer shouldReceiveTouch:(UITouch *)touch {
    return !self.panel && ![touch.view isDescendantOfView:self.button];
}
- (void)start {
    UIView *host = hostView();
    if (!host || self.panel) return;
    if (!self.pip || self.lastFrame <= 0 || CACurrentMediaTime() - self.lastFrame >= 3.0) {
        UIViewController *presenter = ((UIWindow *)host).rootViewController;
        while (presenter.presentedViewController && !presenter.presentedViewController.isBeingDismissed) presenter = presenter.presentedViewController;
        UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"Husk video PiP" message:!self.pip ? @"iOS has not enabled native PiP for this app session." : @"The PiP module is loaded, but no decoded video frames have reached it. Keep the stream playing and report this message." preferredStyle:UIAlertControllerStyleAlert];
        [alert addAction:[UIAlertAction actionWithTitle:@"OK" style:UIAlertActionStyleDefault handler:nil]];
        [presenter presentViewController:alert animated:YES completion:nil];
        return;
    }
    self.panel = [[UIView alloc] initWithFrame:host.bounds];
    self.panel.backgroundColor = UIColor.blackColor;
    [self.panel.layer addSublayer:self.video];
    self.video.frame = self.panel.bounds;
    self.back = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.back setTitle:@"Back" forState:UIControlStateNormal];
    self.back.tintColor = UIColor.whiteColor;
    [self.back addTarget:self action:@selector(cancel) forControlEvents:UIControlEventTouchUpInside];
    [self.panel addSubview:self.back]; [host addSubview:self.panel];
    self.paused = NO;
    atomic_store(&policy, 1);
    // Keep the original controller alive and warm its attached source with real frames.
    self.submittedVideoFrames = 0; self.startAttempts = 0;
    self.wantsPiP = YES; self.startRequested = NO;
    self.startDeadline = CACurrentMediaTime() + 15.0;
    self.nextStartAttempt = CACurrentMediaTime() + 0.4;
    [self tick];
}
- (void)cancel {
    if (self.pip.isPictureInPictureActive) [self.pip stopPictureInPicture];
    else [self finish];
}
- (void)finish {
    self.wantsPiP = NO; self.startRequested = NO;
    atomic_store(&policy, 0);
    [self.panel removeFromSuperview]; self.panel = nil; self.back = nil;
    [self.video removeFromSuperlayer]; [self.video flushAndRemoveImage];
    // Closing PiP in the background must stop Android/audio, not leave a hidden stream.
    applyPlayback(!atomic_load(&hostBackground));
    [self setLiveAudioMuted:NO];
    self.paused = NO;
    self.controlsVisibleUntil = CACurrentMediaTime() + 3.0;
    [self tick];
}
- (void)pictureInPictureControllerDidStartPictureInPicture:(AVPictureInPictureController *)controller {
    if (controller != self.pip) { [controller stopPictureInPicture]; return; }
    if (!self.panel || !(atomic_load(&policy) & 1)) { [controller stopPictureInPicture]; return; }
    NSLog(@"HuskVideoPiP: video-only PiP started");
    self.startRequested = NO; self.wantsPiP = NO; self.button.hidden = YES;
}
- (void)pictureInPictureControllerWillStopPictureInPicture:(AVPictureInPictureController *)controller {
    NSLog(@"HuskVideoPiP: will stop; paused=%d background=%d frameAge=%.1f", self.paused, atomic_load(&hostBackground), self.lastFrame > 0 ? CACurrentMediaTime() - self.lastFrame : -1.0);
}
- (void)pictureInPictureControllerDidStopPictureInPicture:(AVPictureInPictureController *)controller {
    if (controller != self.pip) return;
    NSLog(@"HuskVideoPiP: stopped; paused=%d background=%d", self.paused, atomic_load(&hostBackground));
    [self finish];
}
- (void)pictureInPictureController:(AVPictureInPictureController *)controller failedToStartPictureInPictureWithError:(NSError *)error {
    if (controller != self.pip || !self.startRequested) return;
    NSLog(@"HuskVideoPiP: attempt %lu failed: %@", (unsigned long)self.startAttempts, error);
    self.startRequested = NO;
    // Retry only the observed transient startup error, within the original user request.
    if (self.panel && [error.domain isEqualToString:@"PGPegasusErrorDomain"] && error.code == -1003 && self.startAttempts < 4 && CACurrentMediaTime() < self.startDeadline) {
        // Keep AVKit's original controller/source alive while its failed request unwinds.
        self.submittedVideoFrames = 0;
        self.nextStartAttempt = CACurrentMediaTime() + 1.0 + 0.5 * self.startAttempts;
        self.wantsPiP = YES;
    } else [self finish];
}
- (void)pictureInPictureController:(AVPictureInPictureController *)controller restoreUserInterfaceForPictureInPictureStopWithCompletionHandler:(void (^)(BOOL))completionHandler {
    completionHandler(hostView() != nil);
}
- (void)setLiveAudioMuted:(BOOL)muted {
    if (!self.audioQueue || self.audioMuted == muted) return;
    if (muted) {
        Float32 volume = 1.0f;
        OSStatus read = AudioQueueGetParameter(self.audioQueue, kAudioQueueParam_Volume, &volume);
        if (read != noErr) { NSLog(@"HuskVideoPiP: cannot read live audio volume: %d", (int)read); return; }
        OSStatus result = AudioQueueSetParameter(self.audioQueue, kAudioQueueParam_Volume, 0.0f);
        if (result == noErr) { self.savedVolume = volume; self.audioMuted = YES; }
        else NSLog(@"HuskVideoPiP: cannot mute live audio: %d", (int)result);
    } else {
        OSStatus result = AudioQueueSetParameter(self.audioQueue, kAudioQueueParam_Volume, self.savedVolume);
        if (result == noErr) self.audioMuted = NO;
        else NSLog(@"HuskVideoPiP: cannot restore live audio: %d", (int)result);
    }
}
- (void)pictureInPictureController:(AVPictureInPictureController *)controller setPlaying:(BOOL)playing {
    if (controller != self.pip) return;
    if (self.paused == !playing) return; // AVKit may repeat its current state, including initial Play.
    NSLog(@"HuskVideoPiP: transport %@; background=%d", playing ? @"resume/reconnect" : @"pause without Android lifecycle", atomic_load(&hostBackground));
    self.paused = !playing;
    // Real pause stops native playback. Resume reconstructs the player from its selected intent.
    atomic_store(&policy, playing ? 1u : 3u);
    if (!playing) {
        [self setLiveAudioMuted:YES];
        applyPlayback(4);
        if (self.timebase) CMTimebaseSetRate(self.timebase, 0.0);
    } else {
        // Discard displayed/queued old samples; the next decoded frame is current live video.
        [self.video flush];
        if (self.timebase) { CMTimebaseSetTime(self.timebase, kCMTimeZero); CMTimebaseSetRate(self.timebase, 1.0); }
        applyPlayback(3);
        [self setLiveAudioMuted:NO];
    }
    [controller invalidatePlaybackState];
}
- (CMTimeRange)pictureInPictureControllerTimeRangeForPlayback:(AVPictureInPictureController *)controller { return CMTimeRangeMake(kCMTimeZero, kCMTimePositiveInfinity); }
- (BOOL)pictureInPictureControllerIsPlaybackPaused:(AVPictureInPictureController *)controller { return self.paused; }
- (void)pictureInPictureController:(AVPictureInPictureController *)controller didTransitionToRenderSize:(CMVideoDimensions)size { }
- (void)pictureInPictureController:(AVPictureInPictureController *)controller skipByInterval:(CMTime)interval completionHandler:(void (^)(void))completion { completion(); }
- (BOOL)pictureInPictureControllerShouldProhibitBackgroundAudioPlayback:(AVPictureInPictureController *)controller { return NO; }
@end
