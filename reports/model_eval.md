# Model evaluation (rolling origin, real publication dates)

Test seasons 2012 to 2024. Each forecast uses a model trained only on seasons published before 1 January of the forecast year. All baselines are reported, without selection.

## Pooled

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 313 | 0.162 | 0.120 | 0.154 | 0.486 |
| pre | trend_only | 313 | 0.155 | 0.112 |  |  |
| pre | persistence | 313 | 0.193 | 0.134 | 0.243 | 0.597 |
| pre | linear_3var | 313 | 0.159 | 0.118 | 0.024 | 0.470 |
| pre | model RMSE vs trend only | | 4.6 % | | | |
| mid | model | 325 | 0.158 | 0.120 | 0.216 | 0.520 |
| mid | trend_only | 325 | 0.154 | 0.111 |  |  |
| mid | persistence | 325 | 0.193 | 0.134 | 0.239 | 0.603 |
| mid | linear_3var | 325 | 0.156 | 0.116 | 0.120 | 0.529 |
| mid | model RMSE vs trend only | | 2.4 % | | | |
| end | model | 325 | 0.155 | 0.114 | 0.310 | 0.603 |
| end | trend_only | 325 | 0.154 | 0.111 |  |  |
| end | persistence | 325 | 0.186 | 0.124 | 0.321 | 0.634 |
| end | linear_3var | 325 | 0.156 | 0.116 | 0.194 | 0.520 |
| end | model RMSE vs trend only | | 0.4 % | | | |

## maize

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 156 | 0.152 | 0.105 | 0.043 | 0.410 |
| pre | trend_only | 156 | 0.140 | 0.093 |  |  |
| pre | persistence | 156 | 0.193 | 0.122 | 0.101 | 0.551 |
| pre | linear_3var | 156 | 0.147 | 0.100 | 0.090 | 0.449 |
| pre | model RMSE vs trend only | | 9.0 % | | | |
| mid | model | 156 | 0.142 | 0.101 | 0.278 | 0.513 |
| mid | trend_only | 156 | 0.140 | 0.093 |  |  |
| mid | persistence | 156 | 0.196 | 0.124 | 0.068 | 0.551 |
| mid | linear_3var | 156 | 0.137 | 0.094 | 0.344 | 0.571 |
| mid | model RMSE vs trend only | | 1.3 % | | | |
| end | model | 156 | 0.140 | 0.096 | 0.331 | 0.551 |
| end | trend_only | 156 | 0.140 | 0.093 |  |  |
| end | persistence | 156 | 0.196 | 0.122 | 0.071 | 0.564 |
| end | linear_3var | 156 | 0.138 | 0.094 | 0.393 | 0.558 |
| end | model RMSE vs trend only | | 0.1 % | | | |

## coffee

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 91 | 0.172 | 0.138 | 0.172 | 0.527 |
| pre | trend_only | 91 | 0.168 | 0.128 |  |  |
| pre | persistence | 91 | 0.202 | 0.153 | 0.267 | 0.582 |
| pre | linear_3var | 91 | 0.169 | 0.135 | 0.011 | 0.484 |
| pre | model RMSE vs trend only | | 2.0 % | | | |
| mid | model | 91 | 0.178 | 0.145 | 0.113 | 0.462 |
| mid | trend_only | 91 | 0.168 | 0.128 |  |  |
| mid | persistence | 91 | 0.202 | 0.153 | 0.267 | 0.582 |
| mid | linear_3var | 91 | 0.175 | 0.139 | -0.145 | 0.462 |
| mid | model RMSE vs trend only | | 5.5 % | | | |
| end | model | 91 | 0.173 | 0.136 | 0.236 | 0.593 |
| end | trend_only | 91 | 0.168 | 0.128 |  |  |
| end | persistence | 91 | 0.191 | 0.142 | 0.379 | 0.648 |
| end | linear_3var | 91 | 0.174 | 0.139 | -0.058 | 0.429 |
| end | model RMSE vs trend only | | 2.7 % | | | |

## cocoa

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 66 | 0.169 | 0.133 | 0.311 | 0.606 |
| pre | trend_only | 66 | 0.168 | 0.132 |  |  |
| pre | persistence | 66 | 0.179 | 0.137 | 0.476 | 0.727 |
| pre | linear_3var | 66 | 0.172 | 0.137 | -0.070 | 0.500 |
| pre | model RMSE vs trend only | | 0.7 % | | | |
| mid | model | 78 | 0.163 | 0.131 | 0.284 | 0.603 |
| mid | trend_only | 78 | 0.163 | 0.128 |  |  |
| mid | persistence | 78 | 0.174 | 0.133 | 0.489 | 0.731 |
| mid | linear_3var | 78 | 0.167 | 0.134 | -0.010 | 0.526 |
| mid | model RMSE vs trend only | | -0.0 % | | | |
| end | model | 78 | 0.160 | 0.127 | 0.357 | 0.718 |
| end | trend_only | 78 | 0.163 | 0.128 |  |  |
| end | persistence | 78 | 0.161 | 0.109 | 0.615 | 0.756 |
| end | linear_3var | 78 | 0.167 | 0.132 | 0.175 | 0.551 |
| end | model RMSE vs trend only | | -2.0 % | | | |
