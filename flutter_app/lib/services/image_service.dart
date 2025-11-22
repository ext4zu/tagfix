import 'dart:typed_data';
import 'package:image/image.dart' as img;

class ImageService {
  /// Resizes the given image bytes to the specified width and height.
  /// First crops the image to a square from the center, then resizes.
  /// Returns the resized image as JPEG bytes.
  Future<List<int>?> resizeImage(List<int> imageBytes, {int width = 500, int height = 500}) async {
    try {
      // Decode the image
      final image = img.decodeImage(Uint8List.fromList(imageBytes));
      if (image == null) return null;

      // Crop to square from center
      final size = image.width < image.height ? image.width : image.height;
      final x = (image.width - size) ~/ 2;
      final y = (image.height - size) ~/ 2;
      
      final cropped = img.copyCrop(image, 
        x: x,
        y: y,
        width: size,
        height: size,
      );

      // Resize the square image to target dimensions
      final resized = img.copyResize(cropped, width: width, height: height);

      // Encode back to JPEG
      return img.encodeJpg(resized);
    } catch (e) {
      print('Error resizing image: $e');
      return null;
    }
  }
}
