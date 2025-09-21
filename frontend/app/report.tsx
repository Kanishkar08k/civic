import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  Image,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { Audio } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface Category {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

// API Service
class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getCategories(): Promise<Category[]> {
    return this.request('/categories');
  }

  async createIssue(data: {
    title: string;
    description: string;
    category_id: string;
    image_base64?: string;
    voice_base64?: string;
    location_lat: number;
    location_long: number;
    address?: string;
    user_id: string;
  }) {
    return this.request('/issues', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

const apiService = new ApiService();

export default function ReportIssue() {
  const [user, setUser] = useState<User | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  
  // Form fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [image, setImage] = useState<string>('');
  const [imageUri, setImageUri] = useState<string>('');
  const [voice, setVoice] = useState<string>('');
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [address, setAddress] = useState<string>('');
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    checkAuthAndLoadData();
    requestPermissions();
  }, []);

  const checkAuthAndLoadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
        await loadCategories();
        await getCurrentLocation();
      } else {
        router.replace('/');
      }
    } catch (error) {
      console.error('Error checking auth:', error);
      router.replace('/');
    }
  };

  const requestPermissions = async () => {
    // Request location permissions
    const { status: locationStatus } = await Location.requestForegroundPermissionsAsync();
    if (locationStatus !== 'granted') {
      Alert.alert('Permission needed', 'Location permission is required to report issues');
    }

    // Request audio permissions
    const { status: audioStatus } = await Audio.requestPermissionsAsync();
    if (audioStatus !== 'granted') {
      Alert.alert('Permission needed', 'Audio permission is required for voice notes');
    }

    // Request camera permissions
    const { status: cameraStatus } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (cameraStatus !== 'granted') {
      Alert.alert('Permission needed', 'Camera permission is required to attach photos');
    }
  };

  const loadCategories = async () => {
    try {
      const categoriesData = await apiService.getCategories();
      setCategories(categoriesData);
      if (categoriesData.length > 0) {
        setSelectedCategory(categoriesData[0].id);
      }
    } catch (error) {
      console.error('Error loading categories:', error);
      Alert.alert('Error', 'Failed to load categories');
    }
  };

  const getCurrentLocation = async () => {
    try {
      const loc = await Location.getCurrentPositionAsync({});
      setLocation(loc);
      
      // Get address from coordinates
      const reverseGeocode = await Location.reverseGeocodeAsync({
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
      });
      
      if (reverseGeocode.length > 0) {
        const addr = reverseGeocode[0];
        const fullAddress = `${addr.street || ''} ${addr.city || ''} ${addr.region || ''}`.trim();
        setAddress(fullAddress);
      }
    } catch (error) {
      console.error('Error getting location:', error);
      Alert.alert('Error', 'Failed to get current location');
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
      base64: true,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      setImageUri(asset.uri);
      setImage(asset.base64 || '');
    }
  };

  const takePhoto = async () => {
    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
      base64: true,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      setImageUri(asset.uri);
      setImage(asset.base64 || '');
    }
  };

  const startRecording = async () => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      
      setRecording(recording);
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Error', 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      
      const uri = recording.getURI();
      if (uri) {
        // For demo purposes, we'll just indicate that voice is recorded
        // In production, you'd convert the audio file to base64
        setVoice('audio_recorded');
      }
      
      setRecording(null);
    } catch (error) {
      console.error('Failed to stop recording:', error);
      Alert.alert('Error', 'Failed to stop recording');
    }
  };

  const handleSubmit = async () => {
    if (!title.trim() || !description.trim() || !selectedCategory || !location || !user) {
      Alert.alert('Error', 'Please fill in all required fields and ensure location is available');
      return;
    }

    setLoading(true);
    try {
      const issueData = {
        title: title.trim(),
        description: description.trim(),
        category_id: selectedCategory,
        image_base64: image || undefined,
        voice_base64: voice || undefined,
        location_lat: location.coords.latitude,
        location_long: location.coords.longitude,
        address: address || undefined,
        user_id: user.id,
      };

      await apiService.createIssue(issueData);
      
      Alert.alert(
        'Success',
        'Issue reported successfully!',
        [{ text: 'OK', onPress: () => router.back() }]
      );
    } catch (error: any) {
      console.error('Error submitting issue:', error);
      Alert.alert('Error', error.message || 'Failed to report issue');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (icon?: string) => {
    const iconMap: { [key: string]: string } = {
      'car': 'car',
      'water-drop': 'water',
      'flash': 'flash',
      'trash': 'trash',
      'shield': 'shield-checkmark',
      'leaf': 'leaf',
      'help-circle': 'help-circle',
    };
    return iconMap[icon || 'help-circle'] || 'help-circle';
  };

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.loadingText}>Loading...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.title}>Report Issue</Text>
        <View style={{ width: 24 }} />
      </View>

      <KeyboardAvoidingView 
        style={{ flex: 1 }} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Category Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Category *</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
              {categories.map((category) => (
                <TouchableOpacity
                  key={category.id}
                  style={[
                    styles.categoryOption,
                    selectedCategory === category.id && styles.categoryOptionSelected
                  ]}
                  onPress={() => setSelectedCategory(category.id)}
                >
                  <Ionicons 
                    name={getCategoryIcon(category.icon) as any}
                    size={24} 
                    color={selectedCategory === category.id ? 'white' : '#007AFF'}
                  />
                  <Text style={[
                    styles.categoryOptionText,
                    selectedCategory === category.id && styles.categoryOptionTextSelected
                  ]}>
                    {category.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Title */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Issue Title *</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Brief description of the issue"
              value={title}
              onChangeText={setTitle}
              maxLength={100}
            />
          </View>

          {/* Description */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Description *</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              placeholder="Detailed description of the issue..."
              value={description}
              onChangeText={setDescription}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
          </View>

          {/* Photo Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Add Photo</Text>
            {imageUri ? (
              <View style={styles.imageContainer}>
                <Image source={{ uri: imageUri }} style={styles.selectedImage} />
                <TouchableOpacity
                  style={styles.removeImageButton}
                  onPress={() => { setImage(''); setImageUri(''); }}
                >
                  <Ionicons name="close-circle" size={24} color="#FF3B30" />
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.photoOptions}>
                <TouchableOpacity style={styles.photoOption} onPress={takePhoto}>
                  <Ionicons name="camera" size={24} color="#007AFF" />
                  <Text style={styles.photoOptionText}>Take Photo</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.photoOption} onPress={pickImage}>
                  <Ionicons name="images" size={24} color="#007AFF" />
                  <Text style={styles.photoOptionText}>Choose from Gallery</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>

          {/* Voice Note Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Voice Note (Optional)</Text>
            <View style={styles.voiceContainer}>
              {voice ? (
                <View style={styles.voiceRecorded}>
                  <Ionicons name="mic" size={20} color="#34C759" />
                  <Text style={styles.voiceRecordedText}>Voice note recorded</Text>
                  <TouchableOpacity onPress={() => setVoice('')}>
                    <Ionicons name="trash" size={20} color="#FF3B30" />
                  </TouchableOpacity>
                </View>
              ) : (
                <TouchableOpacity
                  style={[styles.recordButton, isRecording && styles.recordButtonActive]}
                  onPress={isRecording ? stopRecording : startRecording}
                >
                  <Ionicons 
                    name={isRecording ? "stop" : "mic"} 
                    size={24} 
                    color={isRecording ? "#FF3B30" : "#007AFF"}
                  />
                  <Text style={[styles.recordButtonText, isRecording && styles.recordButtonTextActive]}>
                    {isRecording ? "Stop Recording" : "Record Voice Note"}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          </View>

          {/* Location Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Location</Text>
            <View style={styles.locationContainer}>
              <Ionicons name="location" size={20} color="#007AFF" />
              <View style={styles.locationInfo}>
                <Text style={styles.locationText}>
                  {address || 'Getting location...'}
                </Text>
                <TouchableOpacity onPress={getCurrentLocation} style={styles.refreshLocation}>
                  <Ionicons name="refresh" size={16} color="#007AFF" />
                  <Text style={styles.refreshLocationText}>Refresh</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          {/* Submit Button */}
          <TouchableOpacity
            style={[styles.submitButton, loading && styles.submitButtonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <Text style={styles.submitButtonText}>Reporting...</Text>
            ) : (
              <Text style={styles.submitButtonText}>Report Issue</Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  loadingText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#8E8E93',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E7',
  },
  backButton: {
    padding: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  content: {
    flex: 1,
  },
  section: {
    padding: 16,
    backgroundColor: 'white',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  categoryScroll: {
    marginHorizontal: -4,
  },
  categoryOption: {
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 12,
    marginHorizontal: 4,
    minWidth: 80,
  },
  categoryOptionSelected: {
    backgroundColor: '#007AFF',
  },
  categoryOptionText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#007AFF',
    marginTop: 4,
    textAlign: 'center',
  },
  categoryOptionTextSelected: {
    color: 'white',
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#E5E5E7',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#1C1C1E',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  imageContainer: {
    position: 'relative',
  },
  selectedImage: {
    width: '100%',
    height: 200,
    borderRadius: 12,
  },
  removeImageButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'white',
    borderRadius: 12,
  },
  photoOptions: {
    flexDirection: 'row',
    gap: 12,
  },
  photoOption: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 16,
    gap: 8,
  },
  photoOptionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#007AFF',
  },
  voiceContainer: {
    alignItems: 'center',
  },
  voiceRecorded: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F9FF',
    borderRadius: 12,
    padding: 16,
    gap: 12,
    width: '100%',
  },
  voiceRecordedText: {
    flex: 1,
    fontSize: 14,
    color: '#34C759',
    fontWeight: '500',
  },
  recordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 16,
    gap: 12,
    width: '100%',
  },
  recordButtonActive: {
    backgroundColor: '#FFF2F0',
  },
  recordButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#007AFF',
  },
  recordButtonTextActive: {
    color: '#FF3B30',
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  locationInfo: {
    flex: 1,
  },
  locationText: {
    fontSize: 14,
    color: '#1C1C1E',
    fontWeight: '500',
  },
  refreshLocation: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 4,
  },
  refreshLocationText: {
    fontSize: 12,
    color: '#007AFF',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    margin: 16,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});