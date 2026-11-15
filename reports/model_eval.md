# Model evaluation (rolling origin, real publication dates)

Test seasons 2012 to 2024. Each forecast uses a model trained only on seasons published before 1 January of the forecast year. All baselines are reported, without selection.

## Pooled

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 313 | 0.157 | 0.114 | 0.177 | 0.527 |
| pre | trend_only | 313 | 0.155 | 0.112 |  |  |
| pre | persistence | 313 | 0.193 | 0.134 | 0.243 | 0.597 |
| pre | linear_3var | 313 | 0.159 | 0.118 | 0.037 | 0.470 |
| pre | model RMSE vs trend only | | 1.3 % | | | |
| pre | same, weighted by share of world output (headline) | | -1.1 % | | | |
| mid | model | 325 | 0.151 | 0.110 | 0.286 | 0.600 |
| mid | trend_only | 325 | 0.154 | 0.111 |  |  |
| mid | persistence | 325 | 0.193 | 0.134 | 0.239 | 0.603 |
| mid | linear_3var | 325 | 0.155 | 0.115 | 0.193 | 0.526 |
| mid | model RMSE vs trend only | | -1.9 % | | | |
| mid | same, weighted by share of world output (headline) | | -1.3 % | | | |
| end | model | 325 | 0.147 | 0.106 | 0.377 | 0.612 |
| end | trend_only | 325 | 0.154 | 0.111 |  |  |
| end | persistence | 325 | 0.186 | 0.124 | 0.321 | 0.634 |
| end | linear_3var | 325 | 0.154 | 0.114 | 0.248 | 0.542 |
| end | model RMSE vs trend only | | -4.2 % | | | |
| end | same, weighted by share of world output (headline) | | -6.7 % | | | |

## maize

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 156 | 0.150 | 0.098 | 0.010 | 0.474 |
| pre | trend_only | 156 | 0.140 | 0.093 |  |  |
| pre | persistence | 156 | 0.193 | 0.122 | 0.101 | 0.551 |
| pre | linear_3var | 156 | 0.148 | 0.101 | 0.110 | 0.449 |
| pre | model RMSE vs trend only | | 7.2 % | | | |
| pre | same, weighted by share of world output (headline) | | 1.3 % | | | |
| mid | model | 156 | 0.140 | 0.091 | 0.282 | 0.609 |
| mid | trend_only | 156 | 0.140 | 0.093 |  |  |
| mid | persistence | 156 | 0.196 | 0.124 | 0.068 | 0.551 |
| mid | linear_3var | 156 | 0.135 | 0.092 | 0.418 | 0.558 |
| mid | model RMSE vs trend only | | 0.2 % | | | |
| mid | same, weighted by share of world output (headline) | | -6.1 % | | | |
| end | model | 156 | 0.139 | 0.089 | 0.327 | 0.596 |
| end | trend_only | 156 | 0.140 | 0.093 |  |  |
| end | persistence | 156 | 0.196 | 0.122 | 0.071 | 0.564 |
| end | linear_3var | 156 | 0.135 | 0.091 | 0.495 | 0.577 |
| end | model RMSE vs trend only | | -0.6 % | | | |
| end | same, weighted by share of world output (headline) | | -7.4 % | | | |

## coffee

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 91 | 0.161 | 0.128 | 0.237 | 0.516 |
| pre | trend_only | 91 | 0.168 | 0.128 |  |  |
| pre | persistence | 91 | 0.202 | 0.153 | 0.267 | 0.582 |
| pre | linear_3var | 91 | 0.169 | 0.135 | 0.041 | 0.484 |
| pre | model RMSE vs trend only | | -4.2 % | | | |
| pre | same, weighted by share of world output (headline) | | -0.9 % | | | |
| mid | model | 91 | 0.162 | 0.130 | 0.250 | 0.549 |
| mid | trend_only | 91 | 0.168 | 0.128 |  |  |
| mid | persistence | 91 | 0.202 | 0.153 | 0.267 | 0.582 |
| mid | linear_3var | 91 | 0.174 | 0.139 | -0.035 | 0.462 |
| mid | model RMSE vs trend only | | -3.8 % | | | |
| mid | same, weighted by share of world output (headline) | | 1.4 % | | | |
| end | model | 91 | 0.157 | 0.124 | 0.331 | 0.560 |
| end | trend_only | 91 | 0.168 | 0.128 |  |  |
| end | persistence | 91 | 0.191 | 0.142 | 0.379 | 0.648 |
| end | linear_3var | 91 | 0.172 | 0.138 | 0.020 | 0.484 |
| end | model RMSE vs trend only | | -7.0 % | | | |
| end | same, weighted by share of world output (headline) | | -7.0 % | | | |

## cocoa

| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |
|---|---|---|---|---|---|---|
| pre | model | 66 | 0.165 | 0.131 | 0.341 | 0.667 |
| pre | trend_only | 66 | 0.168 | 0.132 |  |  |
| pre | persistence | 66 | 0.179 | 0.137 | 0.476 | 0.727 |
| pre | linear_3var | 66 | 0.172 | 0.138 | -0.093 | 0.500 |
| pre | model RMSE vs trend only | | -1.2 % | | | |
| pre | same, weighted by share of world output (headline) | | -2.2 % | | | |
| mid | model | 78 | 0.159 | 0.127 | 0.327 | 0.641 |
| mid | trend_only | 78 | 0.163 | 0.128 |  |  |
| mid | persistence | 78 | 0.174 | 0.133 | 0.489 | 0.731 |
| mid | linear_3var | 78 | 0.167 | 0.133 | 0.102 | 0.538 |
| mid | model RMSE vs trend only | | -2.4 % | | | |
| mid | same, weighted by share of world output (headline) | | -1.3 % | | | |
| end | model | 78 | 0.153 | 0.120 | 0.487 | 0.705 |
| end | trend_only | 78 | 0.163 | 0.128 |  |  |
| end | persistence | 78 | 0.161 | 0.109 | 0.615 | 0.756 |
| end | linear_3var | 78 | 0.167 | 0.132 | 0.112 | 0.538 |
| end | model RMSE vs trend only | | -6.2 % | | | |
| end | same, weighted by share of world output (headline) | | -6.2 % | | | |
