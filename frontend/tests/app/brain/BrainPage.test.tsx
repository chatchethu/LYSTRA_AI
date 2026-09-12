import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BrainPage from '../../../app/(dashboard)/brain/page';
import { useAuth } from '../../../components/auth/AuthProvider';
import { memoryClient } from '../../../lib/api/memory';
import { useToast } from '../../../components/ui/ToastContext';

jest.mock('../../../components/auth/AuthProvider', () => ({
  useAuth: jest.fn(),
}));

jest.mock('../../../lib/api/memory', () => ({
  memoryClient: {
    list: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock('../../../components/ui/ToastContext', () => ({
  useToast: jest.fn(),
}));

describe('BrainPage', () => {
  beforeEach(() => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: true, token: 'test-token' });
    (useToast as jest.Mock).mockReturnValue({ showToast: jest.fn(), showErrorToast: jest.fn() });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders and fetches memories', async () => {
    const mockMemories = [
      { id: '1', content: 'User likes red', memory_type: 'preference', importance: 0.9, source: 'chat' }
    ];
    (memoryClient.list as jest.Mock).mockResolvedValue(mockMemories);

    render(<BrainPage />);

    await waitFor(() => {
      expect(screen.getByText('"User likes red"')).toBeInTheDocument();
    });
    
    expect(memoryClient.list).toHaveBeenCalledWith(undefined);
  });
});
