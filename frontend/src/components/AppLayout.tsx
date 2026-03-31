import { Box, IconButton } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import type { ReactNode } from 'react';
import TopNavBar from './TopNavBar';

interface AppLayoutProps {
  chatPanel: ReactNode;
  mapPanel: ReactNode;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onSignOut: () => void;
}

export default function AppLayout({ chatPanel, mapPanel, sidebarOpen, onToggleSidebar, onSignOut }: AppLayoutProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
      }}
    >
      <TopNavBar onSignOut={onSignOut} />

      {/* Main content area below nav */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      {/* Chat Sidebar — animate width instead of unmounting */}
      <Box
        sx={{
          width: sidebarOpen ? '30%' : 0,
          minWidth: sidebarOpen ? 360 : 0,
          maxWidth: sidebarOpen ? 480 : 0,
          height: '100%',
          borderRight: sidebarOpen ? '1px solid' : 'none',
          borderColor: 'divider',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          transition: 'width 300ms ease-in-out, min-width 300ms ease-in-out, max-width 300ms ease-in-out',
        }}
      >
        {chatPanel}
      </Box>

      {/* Map Panel */}
      <Box
        sx={{
          flex: 1,
          height: '100%',
          position: 'relative',
        }}
      >
        {/* Toggle button when sidebar is hidden */}
        {!sidebarOpen && (
          <IconButton
            onClick={onToggleSidebar}
            sx={{
              position: 'absolute',
              top: 16,
              left: 16,
              zIndex: 1000,
              bgcolor: 'background.paper',
              boxShadow: '0 2px 4px rgba(0,0,0,0.14)',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              '&:hover': {
                bgcolor: 'background.paper',
                boxShadow: '0 4px 8px rgba(0,0,0,0.16)',
              },
            }}
          >
            <MenuIcon />
          </IconButton>
        )}
        {mapPanel}
      </Box>
      </Box>
    </Box>
  );
}
