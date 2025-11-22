import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/audio_file.dart';
import '../providers/app_state.dart';
import '../services/ffmpeg_service.dart';
import 'cover_art_widget.dart';
import 'lyrics_widget.dart';

class EditorPanel extends StatefulWidget {
  final AudioFile file;

  const EditorPanel({super.key, required this.file});

  @override
  State<EditorPanel> createState() => _EditorPanelState();
}

class _EditorPanelState extends State<EditorPanel> {
  late TextEditingController _filenameController;
  late TextEditingController _titleController;
  late TextEditingController _artistController;
  late TextEditingController _albumController;
  late TextEditingController _yearController;
  late TextEditingController _genreController;
  late TextEditingController _trackController;
  late TextEditingController _discController;

  bool _hasUnsavedChanges = false;

  @override
  void initState() {
    super.initState();
    _initControllers();
  }

  @override
  void didUpdateWidget(covariant EditorPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Only reinitialize controllers if the file path has changed (different file selected)
    // Don't reset on state changes like pending changes - that would wipe unsaved edits
    if (oldWidget.file.path != widget.file.path) {
      _initControllers();
    } else if (oldWidget.file.hasPendingChanges != widget.file.hasPendingChanges) {
      _checkForChanges();
    }
  }

  void _initControllers() {
    final tags = widget.file.tags;
    _filenameController = TextEditingController(text: widget.file.filename);
    _titleController = TextEditingController(text: tags?.title ?? '');
    _artistController = TextEditingController(text: tags?.trackArtist ?? '');
    _albumController = TextEditingController(text: tags?.album ?? '');
    _yearController = TextEditingController(text: tags?.year?.toString() ?? '');
    _genreController = TextEditingController(text: tags?.genre ?? '');
    _trackController = TextEditingController(text: tags?.trackNumber?.toString() ?? '');
    _discController = TextEditingController(text: tags?.discNumber?.toString() ?? '');

    // Add listeners to check for changes
    final controllers = [
      _filenameController, _titleController, _artistController, _albumController,
      _yearController, _genreController, _trackController, _discController
    ];
    for (final controller in controllers) {
      controller.addListener(_checkForChanges);
    }
    
    _checkForChanges();
  }

  void _checkForChanges() {
    final tags = widget.file.tags;
    bool hasChanges = false;

    // Check text fields
    if (_filenameController.text != widget.file.filename) hasChanges = true;
    if (_titleController.text != (tags?.title ?? '')) hasChanges = true;
    if (_artistController.text != (tags?.trackArtist ?? '')) hasChanges = true;
    if (_albumController.text != (tags?.album ?? '')) hasChanges = true;
    if (_yearController.text != (tags?.year?.toString() ?? '')) hasChanges = true;
    if (_genreController.text != (tags?.genre ?? '')) hasChanges = true;
    if (_trackController.text != (tags?.trackNumber?.toString() ?? '')) hasChanges = true;
    if (_discController.text != (tags?.discNumber?.toString() ?? '')) hasChanges = true;

    // Check pending changes
    if (widget.file.hasPendingChanges) hasChanges = true;

    if (hasChanges != _hasUnsavedChanges) {
      setState(() => _hasUnsavedChanges = hasChanges);
    }
  }

  @override
  void dispose() {
    _filenameController.dispose();
    _titleController.dispose();
    _artistController.dispose();
    _albumController.dispose();
    _yearController.dispose();
    _genreController.dispose();
    _trackController.dispose();
    _discController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    // Rename if changed
    if (_filenameController.text != widget.file.filename) {
       await context.read<AppState>().renameFile(widget.file, _filenameController.text);
    }

    // Save metadata tags
    await context.read<AppState>().updateTags(
      widget.file,
      title: _titleController.text,
      artist: _artistController.text,
      album: _albumController.text,
      year: _yearController.text,
      genre: _genreController.text,
      trackNumber: _trackController.text,
      discNumber: _discController.text,
    );
    
    // Fetch the latest file state after updateTags (to avoid race condition)
    final latestFile = context.read<AppState>().selectedFile;
    if (latestFile == null) return;
    
    // Save pending changes (cover art and lyrics) with updated file
    await context.read<AppState>().savePendingChanges(latestFile);
    
    if (mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('All changes saved permanently to file'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.file.filename),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16.0),
            child: FilledButton.icon(
              onPressed: _hasUnsavedChanges ? _save : null,
              icon: const Icon(Icons.save),
              label: const Text('Apply Changes'),
              style: FilledButton.styleFrom(
                backgroundColor: _hasUnsavedChanges 
                    ? Theme.of(context).colorScheme.primary 
                    : Theme.of(context).colorScheme.surfaceContainerHighest,
                foregroundColor: _hasUnsavedChanges
                    ? Theme.of(context).colorScheme.onPrimary
                    : Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Cover Art
          Center(
            child: CoverArtWidget(file: widget.file),
          ),
          const SizedBox(height: 24),
          
          // Metadata Fields
          TextField(
            controller: _filenameController,
            decoration: const InputDecoration(labelText: 'Filename', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _titleController,
            decoration: const InputDecoration(labelText: 'Title', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _artistController,
            decoration: const InputDecoration(labelText: 'Artist', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _albumController,
            decoration: const InputDecoration(labelText: 'Album', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _yearController,
                  decoration: const InputDecoration(labelText: 'Year', border: OutlineInputBorder()),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextField(
                  controller: _genreController,
                  decoration: const InputDecoration(labelText: 'Genre', border: OutlineInputBorder()),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _trackController,
                  decoration: const InputDecoration(labelText: 'Track No.', border: OutlineInputBorder()),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextField(
                  controller: _discController,
                  decoration: const InputDecoration(labelText: 'Disc No.', border: OutlineInputBorder()),
                  keyboardType: TextInputType.number,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          
          // Conversion Actions
          const Divider(),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8.0),
            child: Text('Conversion', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
          Wrap(
            spacing: 8,
            children: [
              FilledButton.tonal(
                onPressed: () async {
                   final ffmpeg = FfmpegService();
                   final outputDir = await ffmpeg.convertToWav(widget.file);
                   if (mounted) {
                     if (outputDir != null) {
                       showDialog(
                         context: context,
                         builder: (context) => AlertDialog(
                           title: const Text('Conversion Successful'),
                           content: Column(
                             mainAxisSize: MainAxisSize.min,
                             crossAxisAlignment: CrossAxisAlignment.start,
                             children: [
                               const Text('File converted to WAV format.'),
                               const SizedBox(height: 16),
                               const Text('Output folder:', style: TextStyle(fontWeight: FontWeight.bold)),
                               const SizedBox(height: 8),
                               SelectableText(
                                 outputDir,
                                 style: TextStyle(
                                   fontFamily: 'monospace',
                                   color: Theme.of(context).colorScheme.primary,
                                 ),
                               ),
                             ],
                           ),
                           actions: [
                             TextButton(
                               onPressed: () => Navigator.pop(context),
                               child: const Text('OK'),
                             ),
                           ],
                         ),
                       );
                     } else {
                       ScaffoldMessenger.of(context).showSnackBar(
                         const SnackBar(content: Text('Conversion failed')),
                       );
                     }
                   }
                },
                child: const Text('Convert to WAV'),
              ),
              FilledButton.tonal(
                onPressed: () async {
                   final ffmpeg = FfmpegService();
                   final outputDir = await ffmpeg.convertToFlac(widget.file);
                   if (mounted) {
                     if (outputDir != null) {
                       showDialog(
                         context: context,
                         builder: (context) => AlertDialog(
                           title: const Text('Conversion Successful'),
                           content: Column(
                             mainAxisSize: MainAxisSize.min,
                             crossAxisAlignment: CrossAxisAlignment.start,
                             children: [
                               const Text('File converted to FLAC format.'),
                               const SizedBox(height: 16),
                               const Text('Output folder:', style: TextStyle(fontWeight: FontWeight.bold)),
                               const SizedBox(height: 8),
                               SelectableText(
                                 outputDir,
                                 style: TextStyle(
                                   fontFamily: 'monospace',
                                   color: Theme.of(context).colorScheme.primary,
                                 ),
                               ),
                             ],
                           ),
                           actions: [
                             TextButton(
                               onPressed: () => Navigator.pop(context),
                               child: const Text('OK'),
                             ),
                           ],
                         ),
                       );
                     } else {
                       ScaffoldMessenger.of(context).showSnackBar(
                         const SnackBar(content: Text('Conversion failed')),
                       );
                     }
                   }
                },
                child: const Text('Convert to FLAC'),
              ),
            ],
          ),
          const SizedBox(height: 24),
          
          // Lyrics Section
          const Divider(),
          const SizedBox(height: 16),
          LyricsWidget(file: widget.file),
        ],
      ),
    );
  }
}
