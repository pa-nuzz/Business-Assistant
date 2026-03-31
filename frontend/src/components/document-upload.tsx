'use client';

import { useState } from 'react';
import { documents } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

export default function DocumentUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedDocs, setUploadedDocs] = useState<any[]>([]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      const response = await documents.upload(file, setProgress);
      setUploadedDocs((prev) => [...prev, response]);
    } catch (err) {
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer flex flex-col items-center gap-2"
          >
            <div className="text-4xl">📄</div>
            <p className="text-sm text-gray-600">
              Click to upload PDF, DOCX, or TXT
            </p>
            <Button disabled={uploading} variant="outline">
              {uploading ? 'Uploading...' : 'Select File'}
            </Button>
          </label>
        </div>

        {uploading && (
          <div className="space-y-2">
            <Progress value={progress} />
            <p className="text-sm text-center text-gray-500">{progress}%</p>
          </div>
        )}

        {uploadedDocs.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium">Uploaded Documents</h4>
            {uploadedDocs.map((doc) => (
              <div key={doc.id} className="flex items-center gap-2 text-sm">
                <span className="text-green-500">✓</span>
                {doc.title} ({doc.status})
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
