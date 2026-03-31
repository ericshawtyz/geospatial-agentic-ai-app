import { Box, Typography } from '@mui/material';
import { useEffect, useRef } from 'react';
import Markdown from 'react-markdown';
import type { Message } from '../../types/chat';
import ToolCallDisplay from './ToolCallDisplay';

/** Animated bouncing dots shown while the agent is thinking / calling tools. */
function ThinkingDots() {
  return (
    <Box sx={{ display: 'flex', gap: 0.75, alignItems: 'center', py: 0.5 }}>
      {[0, 1, 2].map((i) => (
        <Box
          key={i}
          sx={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            bgcolor: 'text.secondary',
            animation: 'dotBounce 1.4s infinite ease-in-out both',
            animationDelay: `${i * 0.16}s`,
            '@keyframes dotBounce': {
              '0%, 80%, 100%': { transform: 'scale(0)', opacity: 0.4 },
              '40%': { transform: 'scale(1)', opacity: 1 },
            },
          }}
        />
      ))}
    </Box>
  );
}

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <Box
        sx={{
          p: 2,
          bgcolor: '#F5F5F5',
          borderRadius: 0.5,
          fontSize: '14px',
          color: 'text.secondary',
          lineHeight: 1.6,
        }}
      >
        <Box sx={{ mb: 1 }}>
          Ask me anything about Singapore — <strong>locations</strong>,{' '}
          <strong>property data</strong>, <strong>transport</strong>,{' '}
          <strong>demographics</strong>, and more. I'll show results on the map!
        </Box>
        <Box sx={{ fontSize: '12px', color: 'text.primary' }}>
          Try a <strong>location name</strong>, <strong>address</strong>, or{' '}
          <strong>upload a GeoJSON</strong> file.
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      {messages.map((msg, idx) => {
        // Detect if this is the in-flight streaming message
        const isStreamingMsg =
          isLoading && idx === messages.length - 1 && msg.role === 'assistant';
        const showDots = isStreamingMsg && msg.content.trim() === '';

        return (
          <Box key={msg.id} sx={{ mb: 2 }}>
            <Typography
              sx={{
                fontWeight: 500,
                fontSize: '14px',
                mb: 0.5,
                color: 'text.primary',
              }}
            >
              {msg.role === 'user' ? 'User' : 'Assistant'}
            </Typography>
            <Box
              className="markdown-content"
              sx={{
                p: 2,
                bgcolor: msg.role === 'user' ? '#E0E0E0' : '#F5F5F5',
                borderRadius: 0.5,
                fontSize: '14px',
                lineHeight: 1.5,
                '& p': { m: 0, mb: 1, '&:last-child': { mb: 0 } },
                '& pre': {
                  bgcolor: 'rgba(0,0,0,0.05)',
                  p: 1,
                  borderRadius: 0.5,
                  overflow: 'auto',
                  fontSize: '0.9em',
                },
                '& code': { fontSize: '0.9em' },
                '& table': {
                  borderCollapse: 'collapse',
                  width: '100%',
                  mb: 2,
                  fontSize: '0.9em',
                },
                '& th, & td': {
                  border: '1px solid #ddd',
                  px: 1.5,
                  py: 1,
                  textAlign: 'left',
                },
                '& th': { bgcolor: '#F5F5F5', fontWeight: 600 },
                '& tr:nth-of-type(even)': { bgcolor: '#FAFAFA' },
                '& ul, & ol': { ml: 2.5, mb: 1 },
                '& li': { mb: 0.5 },
              }}
            >
              {showDots ? (
                <ThinkingDots />
              ) : msg.role === 'assistant' ? (
                <Markdown>{msg.content}</Markdown>
              ) : (
                <Typography variant="body2">{msg.content}</Typography>
              )}
            </Box>

            {/* Tool calls display */}
            {msg.tools && msg.tools.length > 0 && (
              <Box sx={{ mt: 1, ml: 2 }}>
                <ToolCallDisplay tools={msg.tools} />
              </Box>
            )}
          </Box>
        );
      })}

      {/* Standalone loading indicator — only when no streaming message exists yet */}
      {isLoading &&
        (messages.length === 0 ||
          messages[messages.length - 1].role !== 'assistant') && (
          <Box sx={{ mb: 2 }}>
            <Typography
              sx={{
                fontWeight: 500,
                fontSize: '14px',
                mb: 0.5,
                color: 'text.primary',
              }}
            >
              Assistant
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: '#F5F5F5',
                borderRadius: 0.5,
                minHeight: 40,
              }}
            >
              <ThinkingDots />
            </Box>
          </Box>
        )}

      <div ref={bottomRef} />
    </Box>
  );
}
