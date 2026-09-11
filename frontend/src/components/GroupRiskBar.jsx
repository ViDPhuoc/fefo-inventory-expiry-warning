import { useId } from "react";
import { number, riskLabel } from "../api";

export default function GroupRiskBar({ group }) {
  const tooltipId = useId();
  const levels = ["Do", "Vang", "Xanh"];
  const total = levels.reduce((sum, level) => sum + group[level], 0);
  // Hiện đủ ba mức, kể cả mức bằng 0 không có đoạn màu để rê chuột.
  return (
    <div className="group-chart">
      <span>{group.ten_nhom}</span>
      <div
        className="risk-bar-target"
        tabIndex={0}
        role="group"
        aria-label={`Phân bố cảnh báo: ${group.ten_nhom}`}
        aria-describedby={tooltipId}
        onKeyDown={(event) => {
          if (event.key === "Escape") event.currentTarget.blur();
        }}
      >
        <div className="stacked" aria-hidden="true">
          {levels.map((level) => (
            <span key={level} className={level}
              style={{ width: `${total ? 100 * group[level] / total : 0}%` }} />
          ))}
        </div>
        <div className="risk-bar-tooltip" id={tooltipId} role="tooltip">
          <strong>{group.ten_nhom}</strong>
          {levels.map((level) => (
            <div className="risk-tooltip-line" key={level}>
              <span><i className={`risk-dot ${level}`} />{riskLabel[level]}</span>
              <b>{number(group[level])} lô</b>
            </div>
          ))}
          <div className="risk-tooltip-total">Tổng: {number(total)} lô</div>
        </div>
      </div>
      <strong title="Tổng số lô của nhóm">{number(total)}</strong>
    </div>
  );
}
