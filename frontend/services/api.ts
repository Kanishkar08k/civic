import { User, Issue, Category, Comment } from '../types';

const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
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

  // Authentication
  async login(email: string, password: string): Promise<{ success: boolean; user: User; message: string }> {
    return this.request('/users/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(name: string, email: string, password: string): Promise<{ success: boolean; user: User; message: string }> {
    return this.request('/users/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
  }

  // Categories
  async getCategories(): Promise<Category[]> {
    return this.request('/categories');
  }

  async initCategories(): Promise<{ success: boolean; message: string }> {
    return this.request('/categories/init', {
      method: 'POST',
    });
  }

  // Issues
  async getIssues(params?: {
    lat?: number;
    lng?: number;
    radius?: number;
    category_id?: string;
    limit?: number;
  }): Promise<Issue[]> {
    const queryParams = new URLSearchParams();
    if (params?.lat) queryParams.append('lat', params.lat.toString());
    if (params?.lng) queryParams.append('lng', params.lng.toString());
    if (params?.radius) queryParams.append('radius', params.radius.toString());
    if (params?.category_id) queryParams.append('category_id', params.category_id);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/issues?${queryString}` : '/issues';
    
    return this.request(endpoint);
  }

  async getIssue(issueId: string): Promise<Issue> {
    return this.request(`/issues/${issueId}`);
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
  }): Promise<{ success: boolean; issue: Issue; message: string }> {
    const formData = new FormData();
    formData.append('user_id', data.user_id);
    
    // Send as JSON in the body for simplicity
    return this.request('/issues', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: data.title,
        description: data.description,
        category_id: data.category_id,
        image_base64: data.image_base64,
        voice_base64: data.voice_base64,
        location_lat: data.location_lat,
        location_long: data.location_long,
        address: data.address,
      }),
    });
  }

  // Voting
  async voteIssue(issueId: string, userId: string): Promise<{ success: boolean; voted: boolean; message: string }> {
    const formData = new FormData();
    formData.append('user_id', userId);

    return this.request(`/issues/${issueId}/vote`, {
      method: 'POST',
      body: formData,
    });
  }

  // Comments
  async getComments(issueId: string): Promise<Comment[]> {
    return this.request(`/issues/${issueId}/comments`);
  }

  async addComment(issueId: string, message: string, userId: string): Promise<{ success: boolean; comment: Comment; message: string }> {
    const formData = new FormData();
    formData.append('user_id', userId);

    return this.request(`/issues/${issueId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        issue_id: issueId,
        message: message,
      }),
    });
  }
}

export const apiService = new ApiService();