import { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";

// const API = "http://localhost:5000/api";
const API = import.meta.env.VITE_API_URL;


const VIDEO_RESOLUTIONS = [
    { label: "Best available", value: "best" },
    { label: "4K (2160p)", value: "2160" },
    { label: "1440p (2K)", value: "1440" },
    { label: "1080p (Full HD)", value: "1080" },
    { label: "720p (HD)", value: "720" },
    { label: "480p", value: "480" },
    { label: "360p", value: "360" },
];

function Icon({ name, size = 16 }) {
    const icons = {
        logo: (
            <path
                d="M12 2l9 4.9V17.1L12 22l-9-4.9V6.9L12 2zM10 8.5v7l6-3.5-6-3.5z"
                fill="currentColor"
            />
        ),
        download: (
            <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
            </g>
        ),
        yt: (
            <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33zM9.75 15.02V8.48l5.75 3.27-5.75 3.27z" fill="currentColor" />
        ),
        video: (
            <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 7l-7 5 7 5V7zM1 5h14v14H1V5z" />
            </g>
        ),
        audio: (
            <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
            </g>
        ),
        warn: (
            <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01" />
            </g>
        ),
        check: (
            <polyline points="20 6 9 17 4 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        ),
        github: (
            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        ),
        linkedin: (
            <>
                <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <circle cx="4" cy="4" r="2" fill="currentColor" />
            </>
        ),
        mail: (
            <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
            </g>
        ),
    };
    return <svg viewBox="0 0 24 24" width={size} height={size} style={{ flexShrink: 0 }}>{icons[name] || null}</svg>;
}

function WaveAnimation({ active }) {
    return (
        <div className={`wave-container ${active ? "active" : ""}`}>
            {[...Array(14)].map((_, i) => (
                <div key={i} className="wave-bar" style={{ "--i": i }} />
            ))}
        </div>
    );
}



function ProgressBar({ progress, status }) {
    const isError = status === "error";
    const isDone = status === "done";
    return (
        <div className="progress-wrapper">
            <div className="progress-header">
                <span className="progress-label">
                    {isError ? "Download failed" : isDone ? "Download complete" : "Downloading…"}
                </span>
                <span className={`progress-pct ${isError ? "err" : isDone ? "ok" : ""}`}>
                    {isError ? "Error" : `${Math.round(progress)}%`}
                </span>
            </div>
            <div className="progress-track">
                <div className={`progress-fill ${isError ? "err" : isDone ? "ok" : ""}`} style={{ width: `${progress}%` }} />
            </div>
        </div>
    );
}



export default function App() {
    const [url, setUrl] = useState("");
    const [mode, setMode] = useState("video");
    const [resolution, setResolution] = useState("best");
    const [jobId, setJobId] = useState(null);
    const [job, setJob] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const inputRef = useRef(null);
    const pollRef = useRef(null);

    const stopPolling = useCallback(() => {
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    }, []);

    const startPolling = useCallback((id) => {
        stopPolling();
        pollRef.current = setInterval(async () => {
            try {
                const res = await fetch(`${API}/progress/${id}`);
                const data = await res.json();
                setJob(data);
                if (data.status === "done" || data.status === "error") { stopPolling(); setLoading(false); }
            } catch { stopPolling(); setLoading(false); setError("Lost connection to server."); }
        }, 600);
    }, [stopPolling]);

    useEffect(() => () => stopPolling(), [stopPolling]);

    const handleDownload = async () => {
        const trimmed = url.trim();
        if (!trimmed) { setError("Please enter a YouTube URL."); inputRef.current?.focus(); return; }
        setError(""); setJob(null); setJobId(null); setLoading(true);
        try {
            const res = await fetch(`${API}/download`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: trimmed, mode, resolution }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "Server error");
            setJobId(data.job_id);
            setJob({ progress: 0, status: "queued" });
            startPolling(data.job_id);
        } catch (e) { setError(e.message); setLoading(false); }
    };



    const handleSave = () => { if (jobId) window.location.href = `${API}/file/${jobId}`; };
    const handleReset = () => {
        stopPolling(); setUrl(""); setJob(null); setJobId(null);
        setLoading(false); setError(""); setResolution("best");
        setTimeout(() => inputRef.current?.focus(), 100);
    };

    const isDone = job?.status === "done";
    const isError = job?.status === "error";
    const isActive = loading && !isDone && !isError;




    return (
        <div className="shell">
            <header className="topbar">
                <div className="topbar-logo">
                    <div className="logo-mark"><Icon name="logo" size={20} /></div>
                    <span className="logo-name">YT Downloader</span>
                </div>
            </header>

            <div className="page-body">
                <div className="center">

                    <section className="section-hero">
                        <h1 className="section-title">Free YouTube Video Downloader</h1>
                        <p className="section-sub">
                            YT Downloader is a YouTube video downloader that makes it easy to save videos or extract audio.
                            It supports multiple formats including MP4 for videos up to 4K and MP3 for audio.
                        </p>
                    </section>

                    
                    <main className="two-col">
                        <div className="card">
                            <span className="card-title">Download Configuration</span>

                            <div className="field">
                                <label className="field-label">YouTube URL</label>
                                <div className="input-wrap">
                                    <input
                                        ref={inputRef}
                                        className="text-input"
                                        type="text"
                                        value={url}
                                        onChange={e => setUrl(e.target.value)}
                                        onKeyDown={e => e.key === "Enter" && !loading && handleDownload()}
                                        placeholder="https://youtube.com/watch?v=..."
                                        disabled={loading}
                                        spellCheck={false}
                                        autoComplete="off"
                                    />
                                    {url && !loading && (
                                        <button className="input-clear" onClick={() => { setUrl(""); setError(""); inputRef.current?.focus(); }}>✕</button>
                                    )}
                                </div>
                            </div>

                            <div className="field">
                                <label className="field-label">Output format</label>
                                <div className="toggle-group">
                                    <button className={`toggle-btn ${mode === "video" ? "active" : ""}`} onClick={() => !loading && setMode("video")} disabled={loading}>
                                        <Icon name="video" size={14} /> Video · MP4
                                    </button>
                                    <button className={`toggle-btn ${mode === "audio" ? "active" : ""}`} onClick={() => !loading && setMode("audio")} disabled={loading}>
                                        <Icon name="audio" size={14} /> Audio · MP3
                                    </button>
                                </div>
                            </div>

                            {mode === "video" && (
                                <div className="field">
                                    <label className="field-label">Resolution</label>
                                    <div className="select-wrap">
                                        <select className="select-input" value={resolution} onChange={e => setResolution(e.target.value)} disabled={loading}>
                                            {VIDEO_RESOLUTIONS.map(r => (
                                                <option key={r.value} value={r.value}>{r.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            )}

                            {error && <div className="alert error"><Icon name="warn" size={14} /> {error}</div>}

                            <div className="card-actions">
                                {!isDone ? (
                                    <button className="btn-primary" onClick={handleDownload} disabled={loading}>
                                        {loading ? <><span className="spinner" />Processing…</> : <><Icon name="download" size={14} />Start Download</>}
                                    </button>
                                ) : (
                                    <button className="btn-primary success" onClick={handleSave}>
                                        <Icon name="download" size={14} /> Save File
                                    </button>
                                )}
                                {(isDone || isError) && (
                                    <button className="btn-ghost" onClick={handleReset}>New Download</button>
                                )}
                            </div>
                        </div>

                        {job && (
                            <div className="card">
                                <div className="card-header">
                                    <span className="card-title">Download Status</span>
                                    <span className={`badge ${job.status}`}>{job.status}</span>
                                </div>
                                <div className="status-body">
                                    <WaveAnimation active={isActive} />
                                    <ProgressBar progress={job.progress} status={job.status} />
                                    <div className="status-table">
                                        <div className="status-row"><span className="sk">Format</span><span className="sv">{mode.toUpperCase()}</span></div>
                                        <div className="status-row"><span className="sk">Status</span><span className={`sv pill ${job.status}`}>{job.status}</span></div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </main>
                    

                    <section className="info-grid">
                        <div className="info-card">
                            <h3>⚡ Faster Downloads</h3>
                            <p>Download videos at maximum speed so you can watch your videos instantly, whenever you want.</p>
                        </div>
                        <div className="info-card">
                            <h3>🎨 User-Friendly Interface</h3>
                            <p>Designed for everyone. Its clean, minimalist layout makes saving videos quick and effortless.</p>
                        </div>
                        <div className="info-card">
                            <h3>💎 High-Quality Downloads</h3>
                            <p>Download in original quality, including 1080p, 1440p, 4K, and more for crisp details.</p>
                        </div>
                        <div className="info-card">
                            <h3>🔄 Versatile Format Options</h3>
                            <p>Save videos in different formats such as MP4, MP3, or WAV, letting you choose what works best.</p>
                        </div>
                        <div className="info-card">
                            <h3>📱 Cross-Platform Support</h3>
                            <p>Compatible with Android, iPhone, Windows, macOS, and Linux via any modern web browser.</p>
                        </div>
                        <div className="info-card">
                            <h3>✨ Multi-Service Support</h3>
                            <p>It's not just for YouTube; download content from Facebook, Instagram, TikTok, Twitter, and more.</p>
                        </div>
                    </section>

                    <section className="how-to-section">
                        <h2 className="sub-heading text-center">How to Download YouTube Videos</h2>
                        <div className="steps-container">
                            <div className="step">
                                <div className="step-num">1</div>
                                <h4>Paste the Link</h4>
                                <p>Copy the video URL from YouTube and paste it into the input field above.</p>
                            </div>
                            <div className="step">
                                <div className="step-num">2</div>
                                <h4>Select Format</h4>
                                <p>Select your preferred format like MP4 (1080p) for video or MP3 for audio.</p>
                            </div>
                            <div className="step">
                                <div className="step-num">3</div>
                                <h4>Download</h4>
                                <p>Once conversion is complete, click the "Save File" button to store it on your device.</p>
                            </div>
                        </div>
                    </section>

                    <section className="faq-section">
                        <h2 className="sub-heading">Frequently Asked Questions</h2>
                        <div className="faq-item">
                            <p className="faq-q">Can I download unlimited YouTube videos?</p>
                            <p className="faq-a">Yes! You can download unlimited videos for personal use at no cost.</p>
                        </div>
                        <div className="faq-item">
                            <p className="faq-q">Which quality can I download?</p>
                            <p className="faq-a">You can download resolutions including 1080p, 1440p, and 4K if the original video supports it.</p>
                        </div>
                        <div className="faq-item">
                            <p className="faq-q">Are there any limits on video length?</p>
                            <p className="faq-a">There are no limits on video length or size. Larger files simply take a few extra moments to process.</p>
                        </div>
                        <div className="faq-item">
                            <p className="faq-q">Can I use this on any device?</p>
                            <p className="faq-a">Yes! YT-Downloader works smoothly on desktops, tablets, and smartphones through any browser.</p>
                        </div>
                    </section>

                    <section className="dev-section">
                        <div className="card dev-card">
                            <h2 className="dev-name">Developed by Hamza OUJJA</h2>
                            <p className="dev-bio">
                                Hello everyone! My name is <strong>Hamza OUJJA</strong>. I am an
                                <strong> Engineer specialized in Data and AI</strong> from France. I develop great
                                applications and intelligent user experiences. Find my profile in the links below:
                            </p>
                            <div className="dev-links">
                                <a href="mailto:hamzaoujja08@gmail.com" className="dev-link">
                                    <Icon name="mail" size={18} /> Email
                                </a>
                                <a href="https://github.com/HamzaOUJJA" target="_blank" rel="noreferrer" className="dev-link">
                                    <Icon name="github" size={18} /> GitHub
                                </a>
                                <a href="https://www.linkedin.com/in/hamza-oujja" target="_blank" rel="noreferrer" className="dev-link">
                                    <Icon name="linkedin" size={18} /> LinkedIn
                                </a>
                            </div>
                        </div>
                    </section>




                    <footer className="footer">
                        <p>© 2024 YT-Download — Premium Video & Audio Extraction. Completely Free Access.</p>
                    </footer>
                </div>
            </div>
        </div>
    );
}