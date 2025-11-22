import 'package:flutter/material.dart';
import 'package:audiotags/audiotags.dart';
import '../models/audio_file.dart';
import '../services/file_service.dart';
import '../services/tag_service.dart';
import '../services/ffmpeg_service.dart';

class AppState extends ChangeNotifier {
  final FileService _fileService = FileService();
  final TagService _tagService = TagService();
  final FfmpegService _ffmpegService = FfmpegService();

  List<AudioFile> _files = [];
  List<AudioFile> get files => _files;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _currentDirectory;
  String? get currentDirectory => _currentDirectory;

  AudioFile? _selectedFile;
  AudioFile? get selectedFile => _selectedFile;
  
  String? _searchQuery;
  String? get searchQuery => _searchQuery;
  
  /// Get filtered files based on search query
  List<AudioFile> get filteredFiles {
    if (_searchQuery == null || _searchQuery!.isEmpty) {
      return _files;
    }
    
    final query = _searchQuery!.toLowerCase();
    return _files.where((file) {
      final title = file.tags?.title?.toLowerCase() ?? '';
      final artist = file.tags?.trackArtist?.toLowerCase() ?? '';
      final album = file.tags?.album?.toLowerCase() ?? '';
      
      return title.contains(query) || 
             artist.contains(query) || 
             album.contains(query);
    }).toList();
  }

  Future<void> scanDirectory(String path) async {
    _isLoading = true;
    _currentDirectory = path;
    notifyListeners();

    _files = await _fileService.scanDirectory(path);
    
    // Load tags for all files (lazy loading could be better for large libraries, but for now load all)
    // Actually, reading tags for thousands of files might be slow. Let's load tags on demand or in background?
    // For now, let's load tags for the first few or just when selected.
    // But the UI needs to show Title/Artist in the list.
    // Let's load tags in batches or parallel.
    
    _isLoading = false;
    notifyListeners();
    
    // Background tag loading
    _loadTags();
  }

  Future<void> _loadTags() async {
    for (int i = 0; i < _files.length; i++) {
      if (_files[i].tags == null) {
        _files[i] = await _tagService.readTags(_files[i]);
        notifyListeners(); // Notify on every update might be too much, maybe throttle?
      }
    }
  }

  void selectFile(AudioFile file) {
    _selectedFile = file;
    notifyListeners();
  }
  
  void setSearchQuery(String? query) {
    _searchQuery = query;
    notifyListeners();
  }

  Future<void> updateTags(AudioFile file, {
    String? title,
    String? artist,
    String? album,
    String? year,
    String? genre,
    String? trackNumber,
    String? discNumber,
  }) async {
    if (file.tags == null) return;

    final newTags = Tag(
      title: title ?? file.tags?.title,
      trackArtist: artist ?? file.tags?.trackArtist,
      album: album ?? file.tags?.album,
      albumArtist: file.tags?.albumArtist,
      year: year != null ? int.tryParse(year) : file.tags?.year,
      genre: genre ?? file.tags?.genre,
      trackNumber: trackNumber != null ? int.tryParse(trackNumber) : file.tags?.trackNumber,
      trackTotal: file.tags?.trackTotal,
      discNumber: discNumber != null ? int.tryParse(discNumber) : file.tags?.discNumber,
      discTotal: file.tags?.discTotal,
      lyrics: file.tags?.lyrics,
      pictures: file.tags?.pictures ?? const [],
    );

    final success = await _tagService.writeTags(file, newTags);
    if (success) {
      final index = _files.indexOf(file);
      if (index != -1) {
        _files[index] = file.copyWith(tags: newTags);
        if (_selectedFile == file) {
          _selectedFile = _files[index];
        }
        notifyListeners();
      }
    }
  }

  Future<void> renameFile(AudioFile file, String newFilename) async {
    final newPath = await _fileService.renameFile(file, newFilename);
    if (newPath != null) {
      final index = _files.indexOf(file);
      if (index != -1) {
        _files[index] = file.copyWith(
          path: newPath,
          filename: newFilename, // Assuming newFilename includes extension or is handled
        );
        if (_selectedFile == file) {
          _selectedFile = _files[index];
        }
        notifyListeners();
      }
    }
  }
  
  /// Reload a file's tags (useful after cover art or lyrics update)
  Future<void> reloadFile(AudioFile file) async {
    final index = _files.indexOf(file);
    if (index != -1) {
      _files[index] = await _tagService.readTags(_files[index]);
      if (_selectedFile == file) {
        _selectedFile = _files[index];
      }
      notifyListeners();
    }
  }
  
  /// Set pending cover art (preview only, not saved to disk)
  void setPendingCover(AudioFile file, List<int> coverBytes) {
    final index = _files.indexOf(file);
    if (index != -1) {
      _files[index] = _files[index].copyWith(pendingCover: coverBytes);
      if (_selectedFile == file) {
        _selectedFile = _files[index];
      }
      notifyListeners();
    }
  }
  
  /// Set pending lyrics (preview only, not saved to disk)
  void setPendingLyrics(AudioFile file, String lyrics) {
    final index = _files.indexOf(file);
    if (index != -1) {
      _files[index] = _files[index].copyWith(pendingLyrics: lyrics);
      if (_selectedFile == file) {
        _selectedFile = _files[index];
      }
      notifyListeners();
    }
  }
  
  /// Save all pending changes to disk (cover art and lyrics)
  Future<bool> savePendingChanges(AudioFile file) async {
    bool success = true;
    
    // Save pending cover art
    if (file.pendingCover != null) {
      final coverSuccess = await _tagService.setCover(file, file.pendingCover!);
      if (!coverSuccess) success = false;
    }
    
    // Save pending lyrics
    if (file.pendingLyrics != null) {
      final lyricsSuccess = await _tagService.setLyrics(file, file.pendingLyrics!);
      if (!lyricsSuccess) success = false;
    }
    
    // Clear pending changes and reload
    if (success) {
      final index = _files.indexOf(file);
      if (index != -1) {
        _files[index] = _files[index].copyWith(
          clearPendingCover: true,
          clearPendingLyrics: true,
        );
        // Reload from disk to get updated tags
        _files[index] = await _tagService.readTags(_files[index]);
        if (_selectedFile == file) {
          _selectedFile = _files[index];
        }
        notifyListeners();
      }
    }
    
    return success;
  }
  
  /// Discard pending changes without saving
  void discardPendingChanges(AudioFile file) {
    final index = _files.indexOf(file);
    if (index != -1) {
      _files[index] = _files[index].copyWith(
        clearPendingCover: true,
        clearPendingLyrics: true,
      );
      if (_selectedFile == file) {
        _selectedFile = _files[index];
      }
      notifyListeners();
    }
  }
  
  Future<void> convertSelectedToWav() async {
      // Implement batch conversion for selected files
  }
}
