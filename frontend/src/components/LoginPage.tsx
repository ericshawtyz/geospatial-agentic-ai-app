import { useState } from 'react';
import { Box, Typography, TextField, Button } from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';

interface LoginPageProps {
  onLogin: () => void;
}

const PASSCODE = 'sgpsday2026';

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [value, setValue] = useState('');
  const [error, setError] = useState(false);
  const [shakeKey, setShakeKey] = useState(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value === PASSCODE) {
      sessionStorage.setItem('authenticated', '1');
      onLogin();
    } else {
      setError(true);
      setShakeKey((k) => k + 1);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#F5F5F5',
      }}
    >
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          width: 380,
          p: 4,
          bgcolor: 'background.paper',
          borderRadius: 2,
          boxShadow: '0 2px 12px rgba(0,0,0,0.12)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2.5,
        }}
      >
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            bgcolor: '#000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <LockOutlinedIcon sx={{ color: '#fff', fontSize: 24 }} />
        </Box>

        <Typography variant="h5" sx={{ fontWeight: 500, fontSize: '22px' }}>
          Geospatial Agentic AI
        </Typography>

        <Typography sx={{ fontSize: '14px', color: 'text.secondary', textAlign: 'center' }}>
          Enter the passcode to continue
        </Typography>

        <TextField
          key={shakeKey}
          fullWidth
          type="password"
          placeholder="Passcode"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setError(false);
          }}
          error={error}
          helperText={error ? 'Invalid passcode' : ' '}
          autoFocus
          size="small"
          sx={{
            ...(error && {
              animation: 'shake 0.4s ease-in-out',
              '@keyframes shake': {
                '0%, 100%': { transform: 'translateX(0)' },
                '10%, 50%, 90%': { transform: 'translateX(-6px)' },
                '30%, 70%': { transform: 'translateX(6px)' },
              },
            }),
          }}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ textTransform: 'none', fontWeight: 500 }}
        >
          Sign In
        </Button>
      </Box>
    </Box>
  );
}
