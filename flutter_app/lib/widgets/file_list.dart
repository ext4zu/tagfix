import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';

class FileList extends StatelessWidget {
  const FileList({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, state, child) {
        if (state.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        final displayFiles = state.filteredFiles;
        
        if (state.files.isEmpty) {
          return const Center(child: Text('No files found'));
        }
        
        if (displayFiles.isEmpty) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.search_off, size: 48, color: Colors.grey),
                SizedBox(height: 16),
                Text('No files match your search'),
              ],
            ),
          );
        }

        return ListView.builder(
          itemCount: displayFiles.length,
          itemBuilder: (context, index) {
            final file = displayFiles[index];
            final isSelected = state.selectedFile == file;

            return ListTile(
              selected: isSelected,
              selectedTileColor: Theme.of(context).colorScheme.primaryContainer,
              selectedColor: Theme.of(context).colorScheme.onPrimaryContainer,
              leading: const Icon(Icons.audio_file),
              title: Text(
                file.tags?.title ?? file.filename,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              subtitle: Text(
                file.tags?.trackArtist ?? 'Unknown Artist',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              onTap: () {
                context.read<AppState>().selectFile(file);
              },
            );
          },
        );
      },
    );
  }
}
