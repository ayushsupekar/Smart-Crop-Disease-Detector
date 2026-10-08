import React, { useState, Component } from 'react';
import { 
  Scan, 
  Camera, 
  UploadCloud, 
  Sparkles, 
  ArrowRight, 
  AlertCircle, 
  MapPin, 
  FileText, 
  RefreshCw,
  Menu
} from 'lucide-react';
import Sidebar from '../components/common/Sidebar';
import Dropzone from '../components/scan/Dropzone';
import CameraCapture from '../components/scan/CameraCapture';
import ScanningAnimation from '../components/scan/ScanningAnimation';
import ScanResultCard from '../components/scan/ScanResultCard';
import { predictLeafDisease } from '../api/scans';

class ScanErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null }; }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  render() {
    if (this.state.hasError) return (
      <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">
        <strong>Result display error:</strong> {this.state.error?.message || 'Unknown error'}
        <button onClick={() => this.setState({ hasError: false, error: null })} className="ml-4 underline text-xs">Try again</button>
      </div>
    );
    return this.props.children;
  }
}

export const ScanPage = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [mode, setMode] = useState('upload'); // 'upload' or 'camera'
  const [detector, setDetector] = useState('leaf');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [fieldLocation, setFieldLocation] = useState('Field Zone A - Greenhouse');
  const [notes, setNotes] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileSelected = (file) => {
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setError('');
    setScanResult(null);
  };

  const clearFile = () => {
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setScanResult(null);
    setError('');
  };

  const handleCameraCapture = (file) => {
    handleFileSelected(file);
    setMode('upload'); // Switch back to review preview
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError("Please select or capture a crop leaf image first.");
      return;
    }

    setError('');
    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('detector', detector);
      formData.append('field_location', fieldLocation);
      if (notes) formData.append('notes', notes);

      const result = await predictLeafDisease(formData);
      setScanResult(result);
    } catch (err) {
      console.error("Analysis failed:", err);
      if (err.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail;
        const detailMsg = Array.isArray(detail)
          ? detail.map((d) => {
              const field = d.loc?.slice(1).join('.');
              return field ? `${field}: ${d.msg}` : (d.msg || JSON.stringify(d));
            }).join('; ')
          : typeof detail === 'string' ? detail : null;
        if (status === 401) setError('Session expired. Please log in again.');
        else if (status === 403) setError('Permission denied.');
        else if (status === 400) setError(detailMsg || 'Invalid image or request.');
        else if (status === 404) setError('The scan endpoint was not found. Verify the deployed backend URL and version.');
        else if (status === 422) setError(detailMsg || 'The scan request is missing required information.');
        else if (status === 413) setError('Image too large. Please upload a smaller file.');
        else if (status === 415) setError(detailMsg || 'Unsupported image type. Upload a JPEG, PNG, or WEBP image.');
        else if (status === 503) setError('ML model unavailable on server. Contact support.');
        else if (status === 502) setError('Backend crashed during inference. Check Render logs.');
        else if (status >= 500) setError(detailMsg || `Backend inference failed (${status}). Check Render logs.`);
        else setError(detailMsg || `Server error (${status}).`);
      } else if (err.request) {
        setError('No response from the API. Check the production API URL, backend availability, and CORS settings.');
      } else {
        setError(err.message || 'Unexpected error.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetAll = () => {
    clearFile();
    setScanResult(null);
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex">
      {/* Dark Sidebar */}
      <Sidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

      {/* Main Content */}
      <main className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Header */}
        <header className="h-20 bg-white border-b border-gray-100 px-6 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-xl text-slate-textMuted hover:bg-gray-100"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-slate-textDark tracking-tight">
                {detector === 'fruit' ? 'Citrus Fruit Disease Diagnostic Studio' : 'Crop Leaf Diagnostic Studio'}
              </h1>
              <p className="text-xs text-slate-textMuted">
                Instant AI Classification & Integrated Pest Management Guidance
              </p>
            </div>
          </div>
        </header>

        <div className="p-6 sm:p-8 space-y-8 max-w-5xl w-full mx-auto">
          {/* If analysis is running, show holographic scanner animation */}
          {isAnalyzing && (
            <ScanningAnimation imagePreview={previewUrl} />
          )}

          {/* If analysis succeeded, show diagnostic result card */}
          {!isAnalyzing && scanResult && (
            <ScanErrorBoundary>
              <ScanResultCard
                result={scanResult}
                onResetScan={resetAll}
              />
            </ScanErrorBoundary>
          )}

          {/* If not analyzing and no result yet, show image intake form */}
          {!isAnalyzing && !scanResult && (
            <div className="space-y-6">
              {/* Header Box */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-gray-100 shadow-soft-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-slate-textDark">
                      {detector === 'fruit' ? 'Select Citrus Fruit Image Intake Method' : 'Select Leaf Image Intake Method'}
                    </h2>
                    <p className="text-xs sm:text-sm text-slate-textMuted">
                      Upload a high-resolution leaf photo or trigger real-time camera capture
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-textMuted">Detect</span>
                    <div className="inline-flex rounded-full bg-gray-100 p-1 border border-gray-200" role="group" aria-label="Detection type">
                      <button
                        type="button"
                        aria-pressed={detector === 'leaf'}
                        onClick={() => setDetector('leaf')}
                        className={`px-4 py-2 rounded-full text-xs font-bold transition-all ${detector === 'leaf' ? 'bg-brand-dark text-white shadow-soft-sm' : 'text-slate-textMuted hover:text-slate-textDark'}`}
                      >
                        Leaf disease
                      </button>
                      <button
                        type="button"
                        aria-pressed={detector === 'fruit'}
                        onClick={() => setDetector('fruit')}
                        className={`px-4 py-2 rounded-full text-xs font-bold transition-all ${detector === 'fruit' ? 'bg-brand-dark text-white shadow-soft-sm' : 'text-slate-textMuted hover:text-slate-textDark'}`}
                      >
                        Citrus disease
                      </button>
                    </div>
                  </div>
                  {detector === 'fruit' && (
                    <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                      Citrus only. This model classifies citrus disease labels; it does not identify fruit species. Other fruits are unsupported and may be misclassified.
                    </p>
                  )}

                  {/* Mode switcher pills */}
                  <div className="inline-flex rounded-full bg-gray-100 p-1 border border-gray-200 self-start sm:self-auto">
                    <button
                      type="button"
                      onClick={() => setMode('upload')}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-full text-xs font-bold transition-all ${
                        mode === 'upload'
                          ? 'bg-brand-dark text-white shadow-soft-sm'
                          : 'text-slate-textMuted hover:text-slate-textDark'
                      }`}
                    >
                      <UploadCloud className="w-4 h-4 text-emerald-400" />
                      <span>Upload / Presets</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setMode('camera')}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-full text-xs font-bold transition-all ${
                        mode === 'camera'
                          ? 'bg-brand-dark text-white shadow-soft-sm'
                          : 'text-slate-textMuted hover:text-slate-textDark'
                      }`}
                    >
                      <Camera className="w-4 h-4 text-emerald-400" />
                      <span>Live Camera</span>
                    </button>
                  </div>
                </div>

                {/* Error Banner */}
                {error && (
                  <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 shrink-0 text-rose-500" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Mode: Camera View */}
                {mode === 'camera' && (
                  <CameraCapture
                    detector={detector}
                    onCapture={handleCameraCapture}
                    onClose={() => setMode('upload')}
                  />
                )}

                {/* Mode: Dropzone View */}
                {mode === 'upload' && (
                  <Dropzone
                    detector={detector}
                    onFileSelected={handleFileSelected}
                    selectedFile={selectedFile}
                    previewUrl={previewUrl}
                    clearFile={clearFile}
                  />
                )}
              </div>

              {/* Field Metadata Card */}
              {previewUrl && (
                <div className="bg-white rounded-3xl p-6 sm:p-8 border border-gray-100 shadow-soft-sm">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-textMuted mb-4">
                    Agricultural Context & Field Metadata
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                    <div>
                      <label className="block text-xs font-bold text-slate-textDark mb-1.5 flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-brand-forest" />
                        Field Zone / Plot Location
                      </label>
                      <select
                        value={fieldLocation}
                        onChange={(e) => setFieldLocation(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-forest bg-white"
                      >
                        <option>Field Zone A - Greenhouse 1</option>
                        <option>Field Zone A - High Tunnel</option>
                        <option>Field Zone B - Potato Furrows</option>
                        <option>Field Zone C - Sweet Corn Plot</option>
                        <option>Vineyard Hillside Slope</option>
                        <option>Orchard Block 7 (Apples)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-textDark mb-1.5 flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-brand-forest" />
                        Scouting Notes (Optional)
                      </label>
                      <input
                        type="text"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="e.g. Heavy morning dew observed on lower third"
                        className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-forest"
                      />
                    </div>
                  </div>

                  {/* Primary Analyze Action Button */}
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={handleAnalyze}
                      disabled={isAnalyzing}
                      className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 rounded-full bg-[#14251B] hover:bg-[#1B3B2B] text-white text-base font-bold shadow-soft-md hover:shadow-soft-xl hover:scale-[1.02] transition-all gap-2"
                    >
                      <Sparkles className="w-5 h-5 text-emerald-400 animate-pulse" />
                      Run AI Pathology Diagnosis
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ScanPage;
