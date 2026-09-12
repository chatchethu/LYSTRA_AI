import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatPage } from '../../../components/chat/ChatPage';
import { useAuth } from '@/components/auth/AuthProvider';
import { conversationsClient } from '@/lib/api/conversations';
import { useChatStore } from '@/store/chatStore';

jest.mock('@/components/auth/AuthProvider', () => ({
  useAuth: jest.fn(),
}));

jest.mock('../../../lib/api/chat', () => ({
  chatClient: {
    streamUrl: jest.fn(),
    getStreamHeaders: jest.fn(),
  },
}));

jest.mock('@/lib/api/conversations', () => ({
  conversationsClient: {
    getMessages: jest.fn(),
  },
}));

jest.mock('@/components/ui/CopyButton', () => ({
  CopyButton: () => null,
}));

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() { }
  unobserve() { }
  disconnect() { }
};

describe('ChatPage Message Reconciliation', () => {
  beforeEach(() => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: true, isAuthLoaded: true });
    useChatStore.setState({
      conversationId: 'test-conv',
      messages: [],
      error: null,
      isGenerating: false,
      streamingStatus: 'idle',
    });
    window.HTMLElement.prototype.scrollIntoView = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
    useChatStore.getState().clearChat();
  });

  it('loads and reconciles messages from DB', async () => {
    const mockMessages = [
      { id: '1', role: 'user', content: 'Hello', created_at: new Date().toISOString() },
      { id: '2', role: 'assistant', content: '{"blocks": [{"type": "text", "data": {"text": "Hi"}}]}', created_at: new Date().toISOString() }
    ];
    (conversationsClient.getMessages as jest.Mock).mockResolvedValue(mockMessages);

    render(<ChatPage conversationId="test-conv" />);

    await waitFor(() => {
      expect(conversationsClient.getMessages).toHaveBeenCalledWith('test-conv');
    });
  });
});
