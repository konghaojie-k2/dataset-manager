"use client";

import React from 'react';
import { StreamProvider } from '@/providers/Stream';
import { A2UIAgentChat } from '@/components/a2ui';
import type { Dataset } from '@/lib/api-extension';

interface A2UIChatPageProps {
  onDatasetSelect?: (dataset: Dataset) => void;
}

export default function A2UIChatPage({ onDatasetSelect }: A2UIChatPageProps): React.ReactNode {
  return (
    <StreamProvider>
      <div className="flex h-screen bg-[#faf8f5]">
        <div className="flex-1 p-4">
          <A2UIAgentChat
            onDatasetSelect={onDatasetSelect}
            className="h-full max-w-4xl mx-auto"
          />
        </div>
      </div>
    </StreamProvider>
  );
}
