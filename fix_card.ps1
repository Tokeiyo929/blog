$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$c = Get-Content 'D:\GitHub\blog\index.html' -Raw -Encoding UTF8

# 替换统一高度块：等高互不遮盖。grid两列拉伸，图片列填满格子且overflow hidden，文本列独立不与图重叠
$override = @'
        /* post-card 统一高度·图文等高不遮盖 */
        .post-card {
            min-height: 150px;
            align-items: stretch;
        }

        .post-card > a {
            display: block;
            aspect-ratio: auto;
            height: 100%;
            min-height: 150px;
            overflow: hidden;
        }

        .post-thumb {
            width: 100%;
            height: 100%;
            min-height: 0;
            object-fit: cover;
            display: block;
        }

        .post-excerpt {
            -webkit-line-clamp: 3;
        }

        .post-body {
            min-width: 0;
            min-height: 150px;
            padding: 16px 18px;
            align-content: start;
        }
'@
$c = [regex]::Replace($c, '(?s)/\* post-card 统一高度 \*/.*?(?=\r?\n    </style>)', $override)
Set-Content 'D:\GitHub\blog\index.html' -Value $c -Encoding UTF8 -NoNewline
Write-Output 'patched'
