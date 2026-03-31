import { Box, Typography, IconButton } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import type { Message } from '../../types/chat';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

interface ChatPanelProps {
  messages: Message[];
  isConnected: boolean;
  isLoading: boolean;
  onSendMessage: (content: string, fileContext?: Record<string, unknown>) => void;
  onToggleSidebar?: () => void;
}

export default function ChatPanel({
  messages,
  isConnected,
  isLoading,
  onSendMessage,
  onToggleSidebar,
}: ChatPanelProps) {
  const handleNearbyMRT = () => {
    // Location is automatically attached to every message by useChat,
    // so just send a natural-language query
    onSendMessage('Find the nearest MRT stations to my current location');
  };
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        p: 2,
        bgcolor: '#F5F5F5',
      }}
    >
      {/* Scrollable area */}
      <Box sx={{ flex: 1, overflowY: 'auto', mb: 2, pr: 1 }}>
        {/* Conversation card */}
        <Box
          sx={{
            p: 2,
            bgcolor: 'background.paper',
            borderRadius: 1,
            boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 2,
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: 500, fontSize: '22px' }}>
              Conversation
            </Typography>
            {onToggleSidebar && (
              <IconButton
                onClick={onToggleSidebar}
                size="small"
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                }}
              >
                <MenuIcon fontSize="small" />
              </IconButton>
            )}
          </Box>

          {/* Messages */}
          <MessageList messages={messages} isLoading={isLoading} />

          {/* Quick actions */}
          <Box sx={{ mt: 3 }}>
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 500, mb: 1, fontSize: '16px' }}
            >
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {[
                { label: 'Nearby MRT', handler: handleNearbyMRT },
                { label: 'Property prices', handler: () => onSendMessage('Show recent private residential property transactions in Orchard Road area') },
                { label: 'Planning areas', handler: () => onSendMessage('Show me the planning area boundaries for Tampines') },
              ].map((action) => (
                <Box
                  key={action.label}
                  component="button"
                  onClick={action.handler}
                  disabled={isLoading}
                  sx={{
                    px: 2,
                    py: 1,
                    bgcolor: isLoading ? 'divider' : 'primary.main',
                    color: 'primary.contrastText',
                    border: 'none',
                    borderRadius: 1,
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    fontWeight: 500,
                    fontSize: '14px',
                    fontFamily: 'inherit',
                    opacity: isLoading ? 0.75 : 1,
                    transition: 'box-shadow 200ms cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: isLoading ? 'none' : '0 1px 3px rgba(0,0,0,0.12)',
                    '&:hover': {
                      boxShadow: isLoading ? 'none' : '0 2px 4px rgba(0,0,0,0.14)',
                    },
                  }}
                >
                  {action.label}
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Input area */}
      <MessageInput onSend={onSendMessage} disabled={!isConnected || isLoading} isLoading={isLoading} />
    </Box>
  );
}
