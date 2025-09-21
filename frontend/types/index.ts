export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  role: string;
  created_at: string;
}

export interface Category {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

export interface Issue {
  id: string;
  user_id: string;
  user_name?: string;
  category_id: string;
  category_name?: string;
  category_icon?: string;
  title: string;
  description: string;
  image_base64?: string;
  voice_base64?: string;
  voice_transcript?: string;
  location_lat: number;
  location_long: number;
  address?: string;
  status: 'pending' | 'in_progress' | 'resolved' | 'escalated';
  expected_completion?: string;
  actual_completion?: string;
  vote_count: number;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  issue_id: string;
  user_id: string;
  user_name?: string;
  message: string;
  created_at: string;
}

export interface Vote {
  id: string;
  issue_id: string;
  user_id: string;
  created_at: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}