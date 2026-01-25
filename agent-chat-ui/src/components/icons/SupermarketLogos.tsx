import React from "react";
import { cn } from "@/lib/utils";

interface SupermarketLogoProps extends React.SVGProps<SVGSVGElement> {
  type?: "dataset" | "skill" | "template"; // 默认为 dataset
  className?: string;
}

export function SupermarketLogo({
  type = "dataset",
  className,
  ...props
}: SupermarketLogoProps) {
  // 品牌主色 (Terracotta)
  const primaryColor = "currentColor"; 

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("text-[#c75b39]", className)}
      {...props}
    >
      {/* 统一的外框底座：抽象的“开放盒子/货架” */}
      <path
        d="M4 9V19C4 20.1046 4.89543 21 6 21H18C19.1046 21 20 20.1046 20 19V9"
        stroke={primaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4 9L12 13L20 9"
        stroke={primaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 13V21"
        stroke={primaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 3L4 9L12 13L20 9L12 3Z"
        stroke={primaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="currentColor"
        fillOpacity="0.1"
      />

      {/* 核心元素：根据类型变化 */}
      {type === "dataset" && (
        // 数据：上方悬浮的抽象数据块/连接点
        <g transform="translate(8, 5) scale(0.35)">
           <path 
             d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" 
             fill={primaryColor} 
           />
           <circle cx="12" cy="12" r="3" fill={primaryColor} />
           <path d="M12 7V9" stroke={primaryColor} strokeWidth="2" strokeLinecap="round"/>
           <path d="M12 15V17" stroke={primaryColor} strokeWidth="2" strokeLinecap="round"/>
           <path d="M7 12H9" stroke={primaryColor} strokeWidth="2" strokeLinecap="round"/>
           <path d="M15 12H17" stroke={primaryColor} strokeWidth="2" strokeLinecap="round"/>
        </g>
      )}

      {type === "skill" && (
        // Skill：上方悬浮的拼图/齿轮元素
        <g transform="translate(8, 5) scale(0.35)">
          <path
            d="M19.43 12.98C19.47 12.66 19.5 12.34 19.5 12C19.5 11.66 19.47 11.34 19.43 11.02L21.54 9.37C21.73 9.22 21.78 8.95 21.66 8.73L19.66 5.27C19.54 5.05 19.27 4.96 19.05 5.05L16.56 6.05C16.04 5.66 15.5 5.32 14.87 5.07L14.5 2.42C14.46 2.18 14.25 2 14 2H10C9.75 2 9.54 2.18 9.5 2.42L9.13 5.07C8.5 5.32 7.96 5.66 7.44 6.05L4.95 5.05C4.73 4.96 4.46 5.05 4.34 5.27L2.34 8.73C2.21 8.95 2.27 9.22 2.46 9.37L4.57 11.02C4.53 11.34 4.5 11.67 4.5 12C4.5 12.33 4.53 12.66 4.57 12.98L2.46 14.63C2.27 14.78 2.21 15.05 2.34 15.27L4.34 18.73C4.46 18.95 4.73 19.04 4.95 18.95L7.44 17.95C7.96 18.34 8.5 18.68 9.13 18.93L9.5 21.58C9.54 21.82 9.75 22 10 22H14C14.25 22 14.46 21.82 14.5 21.58L14.87 18.93C15.5 18.68 16.04 18.34 16.56 17.95L19.05 18.95C19.27 19.04 19.54 18.95 19.66 18.73L21.66 15.27C21.78 15.05 21.73 14.78 21.54 14.63L19.43 12.98ZM12 15.5C10.07 15.5 8.5 13.93 8.5 12C8.5 10.07 10.07 8.5 12 8.5C13.93 8.5 15.5 10.07 15.5 12C15.5 13.93 13.93 15.5 12 15.5Z"
            fill={primaryColor}
          />
        </g>
      )}

      {type === "template" && (
        // Template：上方悬浮的文档元素
        <g transform="translate(8, 5) scale(0.35)">
          <path
            d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM16 18H8V16H16V18ZM16 14H8V12H16V14ZM13 9V3.5L18.5 9H13Z"
            fill={primaryColor}
          />
        </g>
      )}
    </svg>
  );
}
