import { Box, Typography, Button } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';

interface TopNavBarProps {
  onSignOut: () => void;
}

export default function TopNavBar({ onSignOut }: TopNavBarProps) {
  return (
    <Box
      component="nav"
      sx={{
        bgcolor: '#000000',
        color: '#FFFFFF',
        height: 56,
        minHeight: 56,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 3,
        boxShadow: '0 2px 4px rgba(0,0,0,0.14)',
        zIndex: 100,
        position: 'relative',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 500,
            fontSize: '18px',
            letterSpacing: '0.15px',
          }}
        >
          Geospatial Agentic AI
        </Typography>
        <Box sx={{ width: '1px', height: 20, bgcolor: 'rgba(255,255,255,0.3)' }} />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Typography
            sx={{
              fontSize: '13px',
              fontWeight: 400,
              color: 'rgba(255,255,255,0.7)',
              letterSpacing: '0.1px',
            }}
          >
            Powered by Microsoft Foundry
          </Typography>
          <Box
            component="img"
            src="https://teamsdevapp.gallerycdn.vsassets.io/extensions/teamsdevapp/vscode-ai-foundry/0.12.4/1764330328705/Microsoft.VisualStudio.Services.Icons.Default"
            alt="Microsoft Foundry"
            sx={{ height: 28, width: 'auto' }}
          />
        </Box>
      </Box>

      <Button
        onClick={onSignOut}
        size="small"
        startIcon={<LogoutIcon sx={{ fontSize: 16 }} />}
        sx={{
          color: 'rgba(255,255,255,0.7)',
          textTransform: 'none',
          fontSize: '13px',
          fontWeight: 400,
          minWidth: 'auto',
          '&:hover': { color: '#fff', bgcolor: 'rgba(255,255,255,0.08)' },
        }}
      >
        Sign Out
      </Button>
    </Box>
  );
}
