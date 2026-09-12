import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FileAttachment, FilePicker } from '../../../components/chat/FileAttachment';
import { filesClient } from '../../../lib/api/files';

jest.mock('../../../lib/api/files', () => ({
  filesClient: {
    upload: jest.fn(),
  },
}));

describe('FileAttachment and FilePicker', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders FileAttachment correctly', () => {
    const onRemove = jest.fn();
    render(
      <FileAttachment
        file={{
          file_id: '1',
          filename: 'test.png',
          type: 'image',
          status: 'ready',
        }}
        onRemove={onRemove}
      />
    );

    expect(screen.getByText('test.png')).toBeInTheDocument();
    
    // Test remove click
    const removeBtn = screen.getByRole('button');
    fireEvent.click(removeBtn);
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it('handles file upload flow', async () => {
    const onFileAttached = jest.fn();
    (filesClient.upload as jest.Mock).mockResolvedValue({
      file_id: 'real-id',
      filename: 'doc.pdf',
      type: 'pdf',
      status: 'ready',
    });

    render(<FilePicker onFileAttached={onFileAttached} />);

    // In a real browser this input is hidden, but we can find it by test ID or just by getting the input element
    // Actually get by tag name or role is hard since it's hidden, let's use document.querySelector
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['dummy content'], 'doc.pdf', { type: 'application/pdf' });

    // Try to trigger the change event
    fireEvent.change(input, { target: { files: [file] } });

    // Expect optimistic UI update
    expect(onFileAttached).toHaveBeenCalledWith(expect.objectContaining({
      status: 'uploading',
      filename: 'doc.pdf'
    }));

    await waitFor(() => {
      expect(onFileAttached).toHaveBeenLastCalledWith(expect.objectContaining({
        status: 'ready',
        file_id: 'real-id'
      }));
    });
  });
});
