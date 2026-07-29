import { useEffect, useRef } from "react";

interface AudioVisualizerProps {
  analyser: AnalyserNode | null;
  isPlaying: boolean;
  accentColor: string;
}

export function AudioVisualizer({
  analyser,
  isPlaying,
  accentColor,
}: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    const resize = () => {
      const ratio = window.devicePixelRatio || 1;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      canvas.width = width * ratio;
      canvas.height = height * ratio;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    resize();
    window.addEventListener("resize", resize);

    const bufferLength = analyser?.frequencyBinCount ?? 32;
    const dataArray = new Uint8Array(bufferLength);

    const drawStatic = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      context.clearRect(0, 0, width, height);
      context.fillStyle = `${accentColor}33`;
      const barWidth = width / bufferLength;
      for (let index = 0; index < bufferLength; index += 1) {
        const barHeight = height * 0.18;
        context.fillRect(
          index * barWidth,
          height - barHeight,
          barWidth - 2,
          barHeight,
        );
      }
    };

    const draw = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      context.clearRect(0, 0, width, height);

      if (!analyser || !isPlaying || reducedMotion) {
        drawStatic();
        animationRef.current = window.requestAnimationFrame(draw);
        return;
      }

      analyser.getByteFrequencyData(dataArray);
      const barWidth = width / bufferLength;

      for (let index = 0; index < bufferLength; index += 1) {
        const normalized = dataArray[index] / 255;
        const barHeight = Math.max(8, normalized * height * 0.9);
        context.fillStyle = accentColor;
        context.globalAlpha = 0.45 + normalized * 0.55;
        context.fillRect(
          index * barWidth,
          height - barHeight,
          barWidth - 2,
          barHeight,
        );
      }

      context.globalAlpha = 1;
      animationRef.current = window.requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener("resize", resize);
      if (animationRef.current !== null) {
        window.cancelAnimationFrame(animationRef.current);
      }
    };
  }, [accentColor, analyser, isPlaying]);

  return (
    <canvas
      ref={canvasRef}
      className="audio-visualizer"
      role="img"
      aria-label="Audio frequency visualization"
    />
  );
}
