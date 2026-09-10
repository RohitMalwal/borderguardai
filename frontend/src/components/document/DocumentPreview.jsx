import { useEffect, useRef, useState } from 'react';

// Shows the uploaded image with real (client-read) dimensions and, when a face
// bounding box is available from the backend, overlays it scaled to the render.
export default function DocumentPreview({ file, facePrimary }) {
  const [url, setUrl] = useState(null);
  const [dims, setDims] = useState(null); // natural {w,h}
  const [render, setRender] = useState(null); // displayed {w,h}
  const imgRef = useRef(null);

  useEffect(() => {
    if (!file) return;
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);

  const onLoad = (e) => {
    setDims({ w: e.target.naturalWidth, h: e.target.naturalHeight });
    measure();
  };

  const measure = () => {
    const el = imgRef.current;
    if (el) setRender({ w: el.clientWidth, h: el.clientHeight });
  };

  useEffect(() => {
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  const boxStyle = () => {
    if (!facePrimary || !dims || !render) return null;
    const sx = render.w / dims.w;
    const sy = render.h / dims.h;
    return {
      left: facePrimary.x * sx,
      top: facePrimary.y * sy,
      width: facePrimary.width * sx,
      height: facePrimary.height * sy,
    };
  };

  const box = boxStyle();

  return (
    <div className="preview">
      {url && <img ref={imgRef} src={url} alt="Uploaded document" onLoad={onLoad} />}
      {box && <div className="face-box" style={box} />}
      {dims && (
        <div
          style={{
            position: 'absolute',
            bottom: 6,
            right: 8,
            fontSize: 11,
            fontFamily: 'var(--mono)',
            color: 'var(--text-1)',
            background: 'rgba(230,236,245,0.85)',
            color: 'var(--text-1)',
            padding: '2px 7px',
            borderRadius: 5,
          }}
        >
          {dims.w} × {dims.h}px
        </div>
      )}
    </div>
  );
}
