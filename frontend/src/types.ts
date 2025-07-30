export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  conversationId?: string;
  userProfile?: Record<string, any>;
}

export interface SendMessageParams {
  message: string;
  conversationId?: string;
  userProfile?: Record<string, any>;
}

export interface CourseResult {
  course_code?: string;
  title?: string;
  description?: string;
  credits?: number;
  [key: string]: any;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  intent: string;
  course_results?: CourseResult[];
  filters?: Record<string, any>;
  error?: string;
}

export interface ConversationInfo {
  conversation_id: string;
  created_at: string;
  message_count: number;
  last_updated: string;
} 