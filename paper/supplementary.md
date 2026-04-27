## Supplementary Materials

### Table S1: Full Model-Complexity Ablation

\begin{table*}[htbp]
\centering
\caption{Model-complexity ablation: instability ratio ($I$) and beat rate across linear and nonlinear models on 100 repeated 80/20 splits.}
\label{tab:model_complexity}
\begin{tabular}{l l c c c c c}
\toprule
Dataset & Model & MAE (mean $\pm$ SD) & $R^2$ (mean) & $r$ (mean) & $I$ & Beat rate \\
\midrule
MM-TBA & Linear & $0.795 \pm 0.089$ & $-0.067$ & $0.178$ & $2.21$ & $0.80$ \\
 & Ridge & $0.793 \pm 0.089$ & $-0.061$ & $0.183$ & $2.09$ & $0.81$ \\
 & Random Forest & $0.815 \pm 0.081$ & $-0.063$ & $0.196$ & $3.96$ & $0.65$ \\
 & Gradient Boosting & $0.856 \pm 0.095$ & $-0.227$ & $0.129$ & $4.60$ & $0.45$ \\
\midrule
Higher Ed & Linear & $1.695 \pm 0.199$ & $0.041$ & $0.469$ & $0.90$ & $0.83$ \\
 & Ridge & $1.686 \pm 0.195$ & $0.054$ & $0.470$ & $0.84$ & $0.83$ \\
 & Random Forest & $1.193 \pm 0.130$ & $0.521$ & $0.744$ & $0.18$ & $1.00$ \\
 & Gradient Boosting & $1.273 \pm 0.146$ & $0.464$ & $0.711$ & $0.23$ & $1.00$ \\
\midrule
xAPI-Edu & Linear & $0.363 \pm 0.025$ & $0.599$ & $0.786$ & $0.12$ & $1.00$ \\
 & Ridge & $0.357 \pm 0.023$ & $0.626$ & $0.799$ & $0.11$ & $1.00$ \\
 & Random Forest & $0.308 \pm 0.023$ & $0.682$ & $0.830$ & $0.09$ & $1.00$ \\
 & Gradient Boosting & $0.327 \pm 0.024$ & $0.663$ & $0.818$ & $0.10$ & $1.00$ \\
\midrule
Entrance Exam & Linear & $0.598 \pm 0.033$ & $0.438$ & $0.670$ & $0.12$ & $1.00$ \\
 & Ridge & $0.594 \pm 0.032$ & $0.448$ & $0.676$ & $0.11$ & $1.00$ \\
 & Random Forest & $0.612 \pm 0.036$ & $0.372$ & $0.628$ & $0.14$ & $1.00$ \\
 & Gradient Boosting & $0.595 \pm 0.033$ & $0.442$ & $0.671$ & $0.12$ & $1.00$ \\
\midrule
UCI Student & Linear & $2.011 \pm 0.148$ & $0.262$ & $0.530$ & $0.36$ & $1.00$ \\
 & Ridge & $2.010 \pm 0.148$ & $0.263$ & $0.530$ & $0.36$ & $1.00$ \\
 & Random Forest & $2.005 \pm 0.151$ & $0.285$ & $0.548$ & $0.37$ & $1.00$ \\
 & Gradient Boosting & $2.046 \pm 0.151$ & $0.257$ & $0.531$ & $0.41$ & $1.00$ \\
\midrule
Dropout & Linear & $0.206 \pm 0.006$ & $0.651$ & $0.807$ & $0.021$ & $1.00$ \\
 & Ridge & $0.206 \pm 0.006$ & $0.651$ & $0.807$ & $0.021$ & $1.00$ \\
 & Random Forest & $0.153 \pm 0.006$ & $0.684$ & $0.828$ & $0.019$ & $1.00$ \\
 & Gradient Boosting & $0.160 \pm 0.006$ & $0.692$ & $0.832$ & $0.019$ & $1.00$ \\
\midrule
OULAD & Linear & $0.296 \pm 0.002$ & $0.471$ & $0.687$ & $0.010$ & $1.00$ \\
 & Ridge & $0.296 \pm 0.002$ & $0.471$ & $0.687$ & $0.010$ & $1.00$ \\
 & Random Forest & $0.193 \pm 0.003$ & $0.577$ & $0.761$ & $0.009$ & $1.00$ \\
 & Gradient Boosting & $0.203 \pm 0.002$ & $0.610$ & $0.781$ & $0.008$ & $1.00$ \\
\bottomrule
\end{tabular}
\end{table*}
