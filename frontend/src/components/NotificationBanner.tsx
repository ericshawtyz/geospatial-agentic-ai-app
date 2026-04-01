import { Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import type { Notification, NotificationSeverity } from '../hooks/useNotifications';

const severityConfig: Record<
  NotificationSeverity,
  { icon: React.ReactNode; bg: string; border: string; color: string }
> = {
  info: {
    icon: <InfoOutlinedIcon sx={{ fontSize: 18, color: '#1976d2' }} />,
    bg: '#e3f2fd',
    border: '#90caf9',
    color: '#0d47a1',
  },
  success: {
    icon: <CheckCircleOutlineIcon sx={{ fontSize: 18, color: '#2e7d32' }} />,
    bg: '#e8f5e9',
    border: '#a5d6a7',
    color: '#1b5e20',
  },
  error: {
    icon: <ErrorOutlineIcon sx={{ fontSize: 18, color: '#c62828' }} />,
    bg: '#fce4ec',
    border: '#ef9a9a',
    color: '#b71c1c',
  },
};

interface NotificationBannerProps {
  notifications: Notification[];
  onDismiss: (id: number) => void;
}

export default function NotificationBanner({ notifications, onDismiss }: NotificationBannerProps) {
  if (notifications.length === 0) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 56,
        right: 16,
        zIndex: 1400,
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        maxWidth: 360,
      }}
    >
      {notifications.map((n) => {
        const cfg = severityConfig[n.severity];
        return (
          <Box
            key={n.id}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              px: 1.5,
              py: 1,
              bgcolor: cfg.bg,
              border: `1px solid ${cfg.border}`,
              borderRadius: 1,
              boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
              animation: 'slideIn 250ms ease-out',
              '@keyframes slideIn': {
                from: { opacity: 0, transform: 'translateX(40px)' },
                to: { opacity: 1, transform: 'translateX(0)' },
              },
            }}
          >
            {cfg.icon}
            <Typography
              sx={{
                flex: 1,
                fontSize: '13px',
                fontWeight: 500,
                color: cfg.color,
                lineHeight: 1.4,
              }}
            >
              {n.message}
            </Typography>
            <IconButton size="small" onClick={() => onDismiss(n.id)} sx={{ p: 0.25 }}>
              <CloseIcon sx={{ fontSize: 16, color: cfg.color }} />
            </IconButton>
          </Box>
        );
      })}
    </Box>
  );
}
