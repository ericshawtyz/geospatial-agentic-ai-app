import { useState, useCallback } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme';
import AppLayout from './components/AppLayout';
import ChatPanel from './components/chat/ChatPanel';
import MapPanel from './components/map/MapPanel';
import LoginPage from './components/LoginPage';
import NotificationBanner from './components/NotificationBanner';
import { useChat } from './hooks/useChat';
import { useMapCommands, useMapCommandProcessor } from './hooks/useMapCommands';
import { useNotifications } from './hooks/useNotifications';

function App() {
  const [authenticated, setAuthenticated] = useState(
    () => sessionStorage.getItem('authenticated') === '1'
  );

  const handleSignOut = useCallback(() => {
    sessionStorage.removeItem('authenticated');
    setAuthenticated(false);
  }, []);

  if (!authenticated) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <LoginPage onLogin={() => setAuthenticated(true)} />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthenticatedApp onSignOut={handleSignOut} />
    </ThemeProvider>
  );
}

function AuthenticatedApp({ onSignOut }: { onSignOut: () => void }) {
  const { messages, isConnected, isLoading, sendMessage, mapCommands, clearMapCommands } = useChat();
  const { mapState, processCommands } = useMapCommands();
  const { notifications, notify, update, dismiss } = useNotifications();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = useCallback(() => setSidebarOpen((prev) => !prev), []);

  useMapCommandProcessor(mapCommands, processCommands, clearMapCommands);

  // Also allow sending geojson file context as map command directly
  const handleSendMessage = (content: string, fileContext?: Record<string, unknown>) => {
    // If file context contains geojson, render it on the map immediately
    if (fileContext?.type === 'geojson' && fileContext?.geojson) {
      processCommands([
        {
          action: 'addGeoJSON',
          data: {
            geojson: fileContext.geojson,
            style: { color: '#ff6600', weight: 2 },
          },
        },
      ]);
    }
    sendMessage(content, fileContext ?? undefined);
  };

  return (
    <>
      <NotificationBanner notifications={notifications} onDismiss={dismiss} />
      <AppLayout
        sidebarOpen={sidebarOpen}
        onToggleSidebar={toggleSidebar}
        onSignOut={onSignOut}
        chatPanel={
          <ChatPanel
            messages={messages}
            isConnected={isConnected}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onToggleSidebar={toggleSidebar}
            onNotify={notify}
            onNotifyUpdate={update}
          />
        }
        mapPanel={<MapPanel mapState={mapState} />}
      />
    </>
  );
}

export default App;
