import React from "react";

export default function PreviewFile({ url, type }) {
  if (!url) return <p>No preview available</p>;

  if (type.startsWith("image/")) {
    return <img src={url} alt="Preview" className="max-w-full rounded-lg shadow" />;
  }

  if (type === "application/pdf") {
    return (
      <iframe
        src={url}
        title="PDF Preview"
        className="w-full h-96 border rounded"
      ></iframe>
    );
  }

  if (type.startsWith("text/")) {
    return (
      <iframe
        src={url}
        title="Text Preview"
        className="w-full h-64 border rounded bg-gray-50"
      ></iframe>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-blue-600 underline"
    >
      Download File
    </a>
  );
}
