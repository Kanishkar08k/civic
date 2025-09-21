import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Issue } from '../types';

interface IssueCardProps {
  issue: Issue;
  onVote: () => void;
  onPress: () => void;
}

export default function IssueCard({ issue, onVote, onPress }: IssueCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return '#FF9500';
      case 'in_progress':
        return '#007AFF';
      case 'resolved':
        return '#34C759';
      case 'escalated':
        return '#FF3B30';
      default:
        return '#8E8E93';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'in_progress':
        return 'In Progress';
      case 'resolved':
        return 'Resolved';
      case 'escalated':
        return 'Escalated';
      default:
        return 'Unknown';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days}d ago`;
    } else if (hours > 0) {
      return `${hours}h ago`;
    } else {
      return 'Just now';
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

  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <View style={styles.header}>
        <View style={styles.categoryInfo}>
          <Ionicons 
            name={getCategoryIcon(issue.category_icon) as any}
            size={20} 
            color="#007AFF" 
          />
          <Text style={styles.categoryName}>{issue.category_name}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(issue.status) }]}>
          <Text style={styles.statusText}>{getStatusText(issue.status)}</Text>
        </View>
      </View>

      <Text style={styles.title} numberOfLines={2}>
        {issue.title}
      </Text>
      
      <Text style={styles.description} numberOfLines={3}>
        {issue.description}
      </Text>

      {issue.image_base64 && (
        <Image 
          source={{ uri: `data:image/jpeg;base64,${issue.image_base64}` }}
          style={styles.image}
          resizeMode="cover"
        />
      )}

      <View style={styles.footer}>
        <View style={styles.issueInfo}>
          <View style={styles.infoItem}>
            <Ionicons name="person-outline" size={16} color="#8E8E93" />
            <Text style={styles.infoText}>{issue.user_name || 'Anonymous'}</Text>
          </View>
          <View style={styles.infoItem}>
            <Ionicons name="time-outline" size={16} color="#8E8E93" />
            <Text style={styles.infoText}>{formatDate(issue.created_at)}</Text>
          </View>
          {issue.address && (
            <View style={styles.infoItem}>
              <Ionicons name="location-outline" size={16} color="#8E8E93" />
              <Text style={styles.infoText} numberOfLines={1}>{issue.address}</Text>
            </View>
          )}
        </View>
        
        <TouchableOpacity style={styles.voteButton} onPress={onVote}>
          <Ionicons name="heart" size={18} color="#FF3B30" />
          <Text style={styles.voteCount}>{issue.vote_count}</Text>
        </TouchableOpacity>
      </View>

      {issue.voice_transcript && (
        <View style={styles.voiceNote}>
          <Ionicons name="mic" size={16} color="#007AFF" />
          <Text style={styles.voiceText} numberOfLines={2}>
            {issue.voice_transcript}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#007AFF',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'white',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 8,
    lineHeight: 24,
  },
  description: {
    fontSize: 15,
    color: '#3C3C43',
    lineHeight: 20,
    marginBottom: 12,
  },
  image: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  issueInfo: {
    flex: 1,
    gap: 6,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  infoText: {
    fontSize: 13,
    color: '#8E8E93',
    flex: 1,
  },
  voteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF2F0',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
  },
  voteCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FF3B30',
  },
  voiceNote: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F7FF',
    padding: 12,
    borderRadius: 12,
    marginTop: 12,
    gap: 8,
  },
  voiceText: {
    flex: 1,
    fontSize: 14,
    color: '#007AFF',
    fontStyle: 'italic',
  },
});