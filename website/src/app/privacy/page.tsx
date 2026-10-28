export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <h1 className="text-3xl font-bold text-slate-900 mb-6">Privacy Policy</h1>
      <div className="prose prose-slate text-sm text-slate-600 space-y-4">
        <p>
          Your privacy is paramount. This policy describes how we collect, store, and process your information.
        </p>
        <h3 className="text-base font-bold text-slate-800">1. Data Storage & S3 Retention</h3>
        <p>
          Files and media are stored securely in AWS S3 with automated retention policies and PII data scrubbing.
        </p>
        <h3 className="text-base font-bold text-slate-800">2. Real-Time Telemetry</h3>
        <p>
          WebSocket telemetry and connection metrics are ephemeral and managed securely in Redis in-memory stores.
        </p>
      </div>
    </div>
  );
}
