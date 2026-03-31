import { useRef, useCallback } from 'react';
import { IconButton, Tooltip } from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';

interface FileUploadButtonProps {
  onFileSelected: (file: File) => void;
  disabled: boolean;
}

const ACCEPTED_TYPES = [
  '.geojson',
  '.json',
  '.pdf',
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.webp',
  '.mp4',
  '.mov',
].join(',');

export default function FileUploadButton({
  onFileSelected,
  disabled,
}: FileUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileSelected(file);
        // Reset so the same file can be selected again
        e.target.value = '';
      }
    },
    [onFileSelected]
  );

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        onChange={handleChange}
        style={{ display: 'none' }}
      />
      <Tooltip title="Attach file (GeoJSON, image, PDF, video)">
        <IconButton onClick={handleClick} disabled={disabled} size="small">
          <AttachFileIcon />
        </IconButton>
      </Tooltip>
    </>
  );
}
