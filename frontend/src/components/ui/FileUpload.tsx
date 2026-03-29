import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileImage, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  isLoading?: boolean
  accept?: Record<string, string[]>
}

export function FileUpload({ 
  onFileSelect, 
  isLoading = false,
  accept = {
    'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
  }
}: FileUploadProps) {
  const [preview, setPreview] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      setFileName(file.name)
      const reader = new FileReader()
      reader.onload = () => {
        setPreview(reader.result as string)
      }
      reader.readAsDataURL(file)
      onFileSelect(file)
    }
  }, [onFileSelect])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: false,
    disabled: isLoading,
  })

  const clearPreview = (e: React.MouseEvent) => {
    e.stopPropagation()
    setPreview(null)
    setFileName(null)
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        'dropzone relative',
        isDragActive && 'dropzone-active',
        isLoading && 'opacity-50 cursor-not-allowed'
      )}
    >
      <input {...getInputProps()} />
      
      {preview ? (
        <div className="relative">
          <img 
            src={preview} 
            alt="Preview" 
            className="max-h-64 mx-auto rounded-lg shadow-md"
          />
          <button
            onClick={clearPreview}
            className="absolute top-2 right-2 p-1 bg-destructive text-destructive-foreground rounded-full hover:bg-destructive/90"
          >
            <X className="w-4 h-4" />
          </button>
          <p className="mt-3 text-sm text-muted-foreground">{fileName}</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <div className="p-4 bg-primary/10 rounded-full">
            {isDragActive ? (
              <FileImage className="w-8 h-8 text-primary" />
            ) : (
              <Upload className="w-8 h-8 text-primary" />
            )}
          </div>
          <div>
            <p className="text-lg font-medium text-foreground">
              {isDragActive ? 'Drop your floor plan here' : 'Upload Floor Plan'}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Drag & drop or click to select (PNG, JPG, WebP)
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
