import { useState, useCallback } from 'react';
import { Box, Button } from '@mui/material';
import FileUploadButton from './FileUploadButton';
import { uploadFile } from '../../services/api';
import type { NotificationSeverity } from '../../hooks/useNotifications';

interface MessageInputProps {
  onSend: (content: string, fileContext?: Record<string, unknown>) => void;
  disabled: boolean;
  isLoading?: boolean;
  onNotify?: (message: string, severity: NotificationSeverity, durationMs?: number) => number;
  onNotifyUpdate?: (id: number, message: string, severity: NotificationSeverity, durationMs?: number) => void;
}

export default function MessageInput({ onSend, disabled, isLoading, onNotify, onNotifyUpdate }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [pendingFileContext, setPendingFileContext] = useState<Record<string, unknown> | null>(null);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed) return;

    onSend(trimmed, pendingFileContext ?? undefined);
    setInput('');
    setPendingFileContext(null);
  }, [input, onSend, pendingFileContext]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleFileSelected = useCallback(async (file: File) => {
    const nid = onNotify?.(`Uploading ${file.name}...`, 'info', 0) ?? 0;
    try {
      onNotifyUpdate?.(nid, `Processing ${file.name}...`, 'info', 0);
      const result = await uploadFile(file);

      if (result.type === 'error') {
        onNotifyUpdate?.(nid, `Failed: ${(result.message as string) || 'Unknown error'}`, 'error', 5000);
        return;
      }

      setPendingFileContext(result);
      onNotifyUpdate?.(nid, `${file.name} ready`, 'success', 3000);

      if (result.type === 'geojson') {
        setInput(`I've uploaded a GeoJSON file: ${file.name}. Please display it on the map and describe what it contains.`);
      } else {
        setInput(`I've uploaded a file: ${file.name}. Please analyze its contents.`);
      }
    } catch {
      onNotifyUpdate?.(nid, `Upload failed for ${file.name}`, 'error', 5000);
      setInput(`Failed to upload ${file.name}. Please try again.`);
    }
  }, [onNotify, onNotifyUpdate]);

  const canSend = !disabled && input.trim().length > 0;

  return (
    <Box>
      {pendingFileContext && (
        <Box
          sx={{
            mb: 1,
            px: 1.5,
            py: 0.5,
            bgcolor: '#F5F5F5',
            borderRadius: 0.5,
            fontSize: '12px',
            color: 'text.secondary',
          }}
        >
          📎 File attached: {(pendingFileContext as Record<string, string>).filename || 'Unknown'}
        </Box>
      )}
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about Singapore locations, property, transport..."
        disabled={disabled}
        style={{
          width: '100%',
          minHeight: '60px',
          padding: '16px',
          fontSize: '14px',
          fontFamily: 'inherit',
          borderRadius: '4px',
          border: '1px solid #E0E0E0',
          marginBottom: '8px',
          resize: 'vertical',
          backgroundColor: '#FFFFFF',
          color: '#1C1B1F',
          transition: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
          boxSizing: 'border-box',
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#000000';
          e.currentTarget.style.outline = '2px solid #000000';
          e.currentTarget.style.outlineOffset = '0';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = '#E0E0E0';
          e.currentTarget.style.outline = 'none';
        }}
      />
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <Button
          variant="contained"
          onClick={handleSend}
          disabled={!canSend}
          disableElevation
          sx={{
            bgcolor: canSend ? 'primary.main' : 'divider',
            color: 'primary.contrastText',
            fontWeight: 500,
            px: 3,
            py: 1,
            opacity: canSend ? 1 : 0.75,
            boxShadow: canSend ? '0 2px 4px rgba(0,0,0,0.14)' : 'none',
            '&:hover': {
              boxShadow: '0 4px 8px rgba(0,0,0,0.16)',
            },
          }}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </Button>
        <FileUploadButton onFileSelected={handleFileSelected} disabled={disabled} />
        <Box sx={{ flex: 1 }} />
      </Box>
    </Box>
  );
}
