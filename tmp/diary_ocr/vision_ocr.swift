import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    fputs("usage: vision_ocr IMAGE [OUTPUT]\n", stderr)
    exit(2)
}

let imagePath = CommandLine.arguments[1]
let outputPath = CommandLine.arguments.count >= 3 ? CommandLine.arguments[2] : nil
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("cannot load image: \(imagePath)\n", stderr)
    exit(3)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
request.minimumTextHeight = 0.006

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    fputs("vision request failed: \(error)\n", stderr)
    exit(4)
}

let observations = (request.results ?? []).sorted {
    let ay = $0.boundingBox.midY
    let by = $1.boundingBox.midY
    if abs(ay - by) > 0.008 { return ay > by }
    return $0.boundingBox.minX < $1.boundingBox.minX
}

var lines: [String] = []
for observation in observations {
    guard let candidate = observation.topCandidates(1).first else { continue }
    let text = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
    if !text.isEmpty { lines.append(text) }
}
let result = lines.joined(separator: "\n") + "\n"
if let outputPath {
    try result.write(toFile: outputPath, atomically: true, encoding: .utf8)
} else {
    print(result, terminator: "")
}
