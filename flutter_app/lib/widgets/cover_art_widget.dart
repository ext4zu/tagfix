import 'package:flutter/material.dart';
import 'package:audiotags/audiotags.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'dart:io';
import 'dart:typed_data';
import '../models/audio_file.dart';
import '../services/tag_service.dart';
import '../services/musicbrainz_service.dart';
import '../providers/app_state.dart';
import 'cover_search_dialog.dart';
import '../services/image_service.dart';

class CoverArtWidget extends StatelessWidget {
  final AudioFile file;

  const CoverArtWidget({super.key, required this.file});
  
  Future<void> _showOptionsDialog(BuildContext context) async {
    final option = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Update Cover Art'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.folder_open),
              title: const Text('Select from file'),
              subtitle: const Text('Choose an image from your device'),
              onTap: () => Navigator.pop(context, 'file'),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.cloud_download),
              title: const Text('Fetch online'),
              subtitle: const Text('Search MusicBrainz for cover art'),
              onTap: () => Navigator.pop(context, 'online'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );

    if (option == 'file') {
      await _selectFromFile(context);
    } else if (option == 'online') {
      await _fetchOnline(context);
    }
  }
  
  Future<void> _selectFromFile(BuildContext context) async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.image,
    );

    if (result != null && context.mounted) {
      File imageFile = File(result.files.single.path!);
      final bytes = await imageFile.readAsBytes();
      await _applyCover(context, bytes);
    }
  }
  
  Future<void> _fetchOnline(BuildContext context) async {
    final artist = file.tags?.trackArtist ?? '';
    final album = file.tags?.album ?? '';
    
    if (artist.isEmpty || album.isEmpty) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).clearSnackBars();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Artist and Album metadata required for online search'),
            duration: Duration(seconds: 2),
          ),
        );
      }
      return;
    }
    
    final coverData = await showDialog<Uint8List>(
      context: context,
      builder: (context) => CoverSearchDialog(
        initialArtist: artist,
        initialAlbum: album,
      ),
    );
    
    if (coverData != null && context.mounted) {
      await _applyCover(context, coverData);
    }
  }
  
  
  
  Future<void> _applyCover(BuildContext context, List<int> bytes) async {
    if (context.mounted) {
      // Set as pending change (preview only)
      final appState = Provider.of<AppState>(context, listen: false);
      appState.setPendingCover(file, bytes);
      
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Preview applied. Click 'Apply Changes' to save."),
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    // Show pending cover if available, otherwise show saved cover
    final hasPendingCover = file.pendingCover != null;
    final pictures = file.tags?.pictures;
    final hasSavedCover = pictures != null && pictures.isNotEmpty;
    final hasCover = hasPendingCover || hasSavedCover;

    return GestureDetector(
      onTap: () => _showOptionsDialog(context),
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: Stack(
          children: [
            Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: hasPendingCover 
                      ? Theme.of(context).colorScheme.primary  // Highlight pending
                      : Theme.of(context).colorScheme.outline.withOpacity(0.5),
                  width: hasPendingCover ? 3 : 2,
                ),
                image: hasCover
                    ? DecorationImage(
                        image: MemoryImage(
                          hasPendingCover 
                              ? Uint8List.fromList(file.pendingCover!)
                              : pictures!.first.bytes
                        ),
                        fit: BoxFit.cover,
                      )
                    : null,
              ),
              child: !hasCover
                  ? Icon(
                      Icons.music_note,
                      size: 64,
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    )
                  : null,
            ),
            // Overlay icon to indicate clickability
            Positioned(
              bottom: 8,
              right: 8,
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Icon(
                  Icons.edit,
                  size: 20,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
            ),
            
            // Resize Button (Bottom Left)
            if (hasCover)
              Positioned(
                bottom: 8,
                left: 8,
                child: GestureDetector(
                  onTap: () async {
                    // Get current bytes (pending or saved)
                    final currentBytes = hasPendingCover 
                        ? file.pendingCover!
                        : pictures!.first.bytes;
                        
                    // Resize
                    final imageService = ImageService();
                    final resizedBytes = await imageService.resizeImage(currentBytes);
                    
                    if (resizedBytes != null && context.mounted) {
                      await _applyCover(context, resizedBytes);
                      
                      ScaffoldMessenger.of(context).clearSnackBars();
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Cover resized to 500x500 (Preview)'),
                          duration: Duration(seconds: 2),
                        ),
                      );
                    }
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.secondaryContainer,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.compress,
                          size: 16,
                          color: Theme.of(context).colorScheme.onSecondaryContainer,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Resize',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.onSecondaryContainer,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
