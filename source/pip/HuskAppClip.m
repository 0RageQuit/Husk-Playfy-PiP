// SPDX-License-Identifier: GPL-2.0-or-later
// Adapt only Husk's own generated Web Clip profiles when hosted by LiveContainer.
#import <Foundation/Foundation.h>
#import <objc/message.h>
#import <objc/runtime.h>

typedef NSData *(*PropertyListWriter)(id, SEL, id, NSPropertyListFormat,
                                     NSPropertyListWriteOptions, NSError *__autoreleasing *);
static PropertyListWriter originalWriter;

static id routedProfile(id input) {
    if (![input isKindOfClass:NSDictionary.class]) return input;
    BOOL hosted = NSClassFromString(@"LCSharedUtils") != Nil || [NSBundle.mainBundle.bundlePath containsString:@"/Documents/Applications/"];
    if (!hosted) return input;
    NSDictionary *profile = input;
    if (![profile[@"PayloadType"] isEqual:@"Configuration"] ||
        ![profile[@"PayloadIdentifier"] isKindOfClass:NSString.class] ||
        ![profile[@"PayloadIdentifier"] hasPrefix:@"app.husk.clip."]) return input;
    NSArray *contents = profile[@"PayloadContent"];
    if (![contents isKindOfClass:NSArray.class] || contents.count != 1 ||
        ![contents.firstObject isKindOfClass:NSDictionary.class]) return input;
    NSDictionary *clip = contents.firstObject;
    if (![clip[@"PayloadType"] isEqual:@"com.apple.webClip.managed"] ||
        ![clip[@"URL"] isKindOfClass:NSString.class]) return input;
    NSURLComponents *inner = [NSURLComponents componentsWithString:clip[@"URL"]];
    if (![inner.scheme.lowercaseString isEqual:@"husk"] ||
        ![inner.host.lowercaseString isEqual:@"open_app"]) return input;
    BOOL hasImport = NO;
    for (NSURLQueryItem *item in inner.queryItems)
        if ([item.name isEqual:@"unique_identifier"] && item.value.length) hasImport = YES;
    if (!hasImport) return input;

    NSString *guest = NSBundle.mainBundle.bundlePath.lastPathComponent;
    if (![guest.pathExtension.lowercaseString isEqual:@"app"]) return input;
    NSURL *documents = [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory
                                                          inDomains:NSUserDomainMask].firstObject;
    NSString *candidate = documents.URLByDeletingLastPathComponent.lastPathComponent;
    NSString *container = [[NSUUID alloc] initWithUUIDString:candidate] ? candidate : nil;
    NSString *scheme = @"livecontainer";
    Class shared = NSClassFromString(@"LCSharedUtils");
    SEL findHost = NSSelectorFromString(@"getContainerUsingLCSchemeWithFolderName:");
    if (container && [shared respondsToSelector:findHost]) {
        NSString *host = ((id (*)(id, SEL, id))objc_msgSend)(shared, findHost, container);
        if ([host isKindOfClass:NSString.class]) {
            host = host.stringByDeletingPathExtension.lowercaseString;
            if ([host isEqual:@"livecontainer"] || [host isEqual:@"livecontainer2"] ||
                [host isEqual:@"livecontainer3"]) scheme = host;
        }
    }
    NSString *encoded = [[clip[@"URL"] dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0];
    NSURLComponents *outer = [NSURLComponents new];
    outer.scheme = scheme;
    outer.host = @"livecontainer-launch";
    NSMutableArray *query = [NSMutableArray arrayWithObject:[NSURLQueryItem queryItemWithName:@"bundle-name" value:guest]];
    if (container) [query addObject:[NSURLQueryItem queryItemWithName:@"container-folder-name" value:container]];
    [query addObject:[NSURLQueryItem queryItemWithName:@"open-url" value:encoded]];
    outer.queryItems = query;
    if (!outer.URL) return input;

    NSMutableDictionary *updatedClip = [clip mutableCopy];
    updatedClip[@"URL"] = outer.URL.absoluteString;
    updatedClip[@"FullScreen"] = @YES;
    updatedClip[@"IgnoreManifestScope"] = @YES;
    NSMutableDictionary *updatedProfile = [profile mutableCopy];
    updatedProfile[@"PayloadContent"] = @[updatedClip];
    updatedProfile[@"PayloadDescription"] = @"Adds a Home Screen icon that opens this Husk app through LiveContainer.";
    NSLog(@"HuskAppClip: generated fullscreen LiveContainer-routed shortcut using current app IDs");
    return updatedProfile;
}

static NSData *writeProfile(id object, SEL selector, id plist, NSPropertyListFormat format,
                           NSPropertyListWriteOptions options, NSError *__autoreleasing *error) {
    return originalWriter(object, selector, routedProfile(plist), format, options, error);
}

void husk_appclip_install(void) {
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        Method method = class_getClassMethod(NSPropertyListSerialization.class,
            @selector(dataWithPropertyList:format:options:error:));
        if (!method) return;
        originalWriter = (PropertyListWriter)method_getImplementation(method);
        method_setImplementation(method, (IMP)writeProfile);
        NSLog(@"HuskAppClip: built-in Generate App Clip adapter installed");
    });
}
