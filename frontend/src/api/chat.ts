// API endpoint for chat - can be configured via environment variable
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  user_profile?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  intent: string;
  course_results?: Array<Record<string, any>>;
  filters?: Record<string, any>;
  error?: string;
}

export const sendMessage = async (
  request: ChatRequest
): Promise<ChatResponse> => {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
  }

  return await response.json();
};

export const sendMessageStream = async (
  request: ChatRequest,
  onToken: (token: string) => void,
  onMetadata: (metadata: any) => void,
  onComplete: (metadata: any) => void,
  onError: (error: string) => void
): Promise<void> => {
  const response = await fetch(`${API_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            switch (data.type) {
              case 'metadata':
                onMetadata(data);
                break;
              case 'token':
                onToken(data.content);
                break;
              case 'end':
                onComplete(data);
                break;
              case 'error':
                onError(data.error);
                break;
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};

export const getConversations = async (): Promise<Array<{
  conversation_id: string;
  created_at: string;
  message_count: number;
  last_updated: string;
}>> => {
  const response = await fetch(`${API_URL}/conversations`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

export const getConversation = async (conversationId: string): Promise<{
  conversation_id: string;
  created_at: string;
  last_updated: string;
  message_count: number;
  user_profile: Record<string, any>;
  history: Array<{
    type: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
}> => {
  const response = await fetch(`${API_URL}/conversations/${conversationId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

export const deleteConversation = async (conversationId: string): Promise<void> => {
  const response = await fetch(`${API_URL}/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
};