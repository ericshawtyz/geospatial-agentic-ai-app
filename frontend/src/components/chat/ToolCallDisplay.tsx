import { useState } from 'react';
import { Box, Typography } from '@mui/material';
import type { ToolCall } from '../../types/chat';

function ToolCallItem({ tool }: { tool: ToolCall }) {
  const [expanded, setExpanded] = useState(false);

  const statusColor = tool.status === 'executing' ? '#424242' : '#2E7D32';
  const statusText = tool.status === 'executing' ? 'Running' : 'Completed';

  return (
    <Box
      sx={{
        mb: 0.5,
        borderLeft: `3px solid ${statusColor}`,
        pl: 1,
      }}
    >
      <Box
        component="button"
        onClick={() => setExpanded(!expanded)}
        sx={{
          width: '100%',
          textAlign: 'left',
          p: '4px 8px',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontSize: '14px',
          color: 'text.primary',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderRadius: 0.5,
          fontFamily: 'inherit',
          transition: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': { bgcolor: 'rgba(0,0,0,0.04)' },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography sx={{ fontWeight: 500, fontSize: '13px' }}>
            {tool.name}
          </Typography>
          <Typography
            component="span"
            sx={{
              fontSize: '11px',
              fontWeight: 500,
              color: statusColor,
              bgcolor: `${statusColor}20`,
              px: 0.5,
              py: '1px',
              borderRadius: 0.5,
            }}
          >
            {statusText}
          </Typography>
        </Box>
        <Typography
          component="span"
          sx={{
            fontSize: '10px',
            color: 'text.secondary',
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
            display: 'inline-block',
          }}
        >
          ▼
        </Typography>
      </Box>

      {expanded && (
        <Box sx={{ mt: 0.5, ml: 1, p: 2, bgcolor: '#F5F5F5', borderRadius: 0.5 }}>
          {tool.arguments && Object.keys(tool.arguments).length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography
                sx={{ fontWeight: 500, fontSize: '13px', color: 'text.secondary', mb: 0.5 }}
              >
                Input Parameters
              </Typography>
              <Box
                sx={{
                  p: 1,
                  bgcolor: 'background.paper',
                  borderRadius: 0.5,
                  border: '1px solid #E0E0E0',
                }}
              >
                {Object.entries(tool.arguments).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 0.5, fontSize: '12px' }}>
                    <Typography
                      component="span"
                      sx={{ color: 'text.secondary', fontWeight: 500, fontSize: '12px' }}
                    >
                      {key}:
                    </Typography>{' '}
                    <Typography component="span" sx={{ color: 'text.primary', fontSize: '12px' }}>
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          {tool.result && (
            <Box>
              <Typography
                sx={{ fontWeight: 500, fontSize: '13px', color: 'text.secondary', mb: 0.5 }}
              >
                Output
              </Typography>
              <Box
                component="pre"
                sx={{
                  p: 1,
                  bgcolor: 'background.paper',
                  borderRadius: 0.5,
                  fontSize: '11px',
                  overflow: 'auto',
                  maxHeight: '300px',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                  border: '1px solid #E0E0E0',
                  m: 0,
                  color: 'text.primary',
                }}
              >
                {tool.result}
              </Box>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}

export default function ToolCallDisplay({ tools }: { tools: ToolCall[] }) {
  const [expanded, setExpanded] = useState(false);

  if (tools.length === 0) return null;

  // Deduplicate by name + status (keep latest)
  const uniqueTools: ToolCall[] = [];
  const seen = new Set<string>();
  for (const tool of [...tools].reverse()) {
    const key = `${tool.name}:${JSON.stringify(tool.arguments)}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueTools.unshift(tool);
    }
  }

  return (
    <Box
      sx={{
        bgcolor: 'background.paper',
        borderRadius: 1,
        border: '1px solid #E0E0E0',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
      }}
    >
      <Box
        component="button"
        onClick={() => setExpanded(!expanded)}
        sx={{
          width: '100%',
          textAlign: 'left',
          p: '8px 16px',
          bgcolor: '#F5F5F5',
          border: 'none',
          cursor: 'pointer',
          fontWeight: 500,
          fontSize: '13px',
          color: 'text.secondary',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontFamily: 'inherit',
          transition: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': { filter: 'brightness(0.95)' },
        }}
      >
        <span>
          {uniqueTools.length} tool{uniqueTools.length !== 1 ? 's' : ''} executed
        </span>
        <Typography
          component="span"
          sx={{
            fontSize: '12px',
            color: 'text.secondary',
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
            display: 'inline-block',
          }}
        >
          ▼
        </Typography>
      </Box>

      {expanded && (
        <Box sx={{ p: 2, pt: 1 }}>
          {uniqueTools.map((tool, index) => (
            <ToolCallItem key={`${tool.name}-${index}`} tool={tool} />
          ))}
        </Box>
      )}
    </Box>
  );
}
