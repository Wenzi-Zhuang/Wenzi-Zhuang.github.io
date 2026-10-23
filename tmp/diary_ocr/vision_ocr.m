#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
#import <Vision/Vision.h>

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        if (argc < 2) { fprintf(stderr, "usage: vision_ocr IMAGE [OUTPUT]\n"); return 2; }
        NSString *imagePath = [NSString stringWithUTF8String:argv[1]];
        NSString *outputPath = argc >= 3 ? [NSString stringWithUTF8String:argv[2]] : nil;
        NSImage *image = [[NSImage alloc] initWithContentsOfFile:imagePath];
        CGImageRef cgImage = [image CGImageForProposedRect:NULL context:nil hints:nil];
        if (!cgImage) { fprintf(stderr, "cannot load image\n"); return 3; }

        VNRecognizeTextRequest *request = [[VNRecognizeTextRequest alloc] init];
        request.recognitionLevel = VNRequestTextRecognitionLevelAccurate;
        request.usesLanguageCorrection = YES;
        request.recognitionLanguages = @[@"zh-Hans", @"zh-Hant", @"en-US"];
        request.minimumTextHeight = 0.006;
        NSError *error = nil;
        VNImageRequestHandler *handler = [[VNImageRequestHandler alloc] initWithCGImage:cgImage options:@{}];
        if (![handler performRequests:@[request] error:&error]) {
            fprintf(stderr, "vision request failed: %s\n", error.localizedDescription.UTF8String); return 4;
        }
        NSArray<VNRecognizedTextObservation *> *sorted = [request.results sortedArrayUsingComparator:^NSComparisonResult(VNRecognizedTextObservation *a, VNRecognizedTextObservation *b) {
            CGFloat ay = CGRectGetMidY(a.boundingBox), by = CGRectGetMidY(b.boundingBox);
            if (fabs(ay - by) > 0.008) return ay > by ? NSOrderedAscending : NSOrderedDescending;
            CGFloat ax = CGRectGetMinX(a.boundingBox), bx = CGRectGetMinX(b.boundingBox);
            return ax < bx ? NSOrderedAscending : (ax > bx ? NSOrderedDescending : NSOrderedSame);
        }];
        CGFloat leftEdge = 1.0;
        NSMutableArray<NSNumber *> *heights = [NSMutableArray array];
        for (VNRecognizedTextObservation *observation in sorted) {
            leftEdge = MIN(leftEdge, CGRectGetMinX(observation.boundingBox));
            [heights addObject:@(CGRectGetHeight(observation.boundingBox))];
        }
        NSArray<NSNumber *> *sortedHeights = [heights sortedArrayUsingSelector:@selector(compare:)];
        CGFloat medianHeight = sortedHeights.count ? sortedHeights[sortedHeights.count / 2].doubleValue : 0.012;
        NSMutableArray<NSString *> *lines = [NSMutableArray array];
        VNRecognizedTextObservation *previous = nil;
        for (VNRecognizedTextObservation *observation in sorted) {
            VNRecognizedText *candidate = [observation topCandidates:1].firstObject;
            NSString *text = [candidate.string stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
            if (text.length) {
                if (previous) {
                    CGFloat gap = CGRectGetMinY(previous.boundingBox) - CGRectGetMaxY(observation.boundingBox);
                    BOOL indented = CGRectGetMinX(observation.boundingBox) > leftEdge + 0.018;
                    BOOL largeGap = gap > MAX(0.012, medianHeight * 0.75);
                    if ((indented || largeGap) && lines.count && ![lines.lastObject isEqualToString:@""]) {
                        [lines addObject:@""];
                    }
                }
                [lines addObject:text];
                previous = observation;
            }
        }
        NSString *result = [[lines componentsJoinedByString:@"\n"] stringByAppendingString:@"\n"];
        if (outputPath) {
            if (![result writeToFile:outputPath atomically:YES encoding:NSUTF8StringEncoding error:&error]) {
                fprintf(stderr, "write failed: %s\n", error.localizedDescription.UTF8String); return 5;
            }
        } else {
            fputs(result.UTF8String, stdout);
        }
    }
    return 0;
}
