"""Muon optimiser for weight matrices (momentum, then an orthogonalised update).

Follows the public reference version: Newton-Schulz iteration with the quintic
coefficients (3.4445, -4.7750, 2.0315), Nesterov momentum 0.95, and the update
scaled by sqrt(max(1, rows / cols)).
"""
import torch


def zeropower(G, steps=5):
    a, b, c = 3.4445, -4.7750, 2.0315
    X = G.bfloat16()
    tall = X.size(0) > X.size(1)
    if tall:
        X = X.T
    X = X / (X.norm() + 1e-7)
    for _ in range(steps):
        A = X @ X.T
        B = b * A + c * A @ A
        X = a * X + B @ X
    return (X.T if tall else X).to(G.dtype)


class Muon(torch.optim.Optimizer):
    def __init__(self, params, lr=0.02, momentum=0.95, nesterov=True, ns_steps=5):
        super().__init__(params, dict(lr=lr, momentum=momentum, nesterov=nesterov, ns_steps=ns_steps))

    @torch.no_grad()
    def step(self):
        for g in self.param_groups:
            for p in g["params"]:
                if p.grad is None:
                    continue
                st = self.state[p]
                if "buf" not in st:
                    st["buf"] = torch.zeros_like(p.grad)
                buf = st["buf"]
                buf.lerp_(p.grad, 1 - g["momentum"])
                u = p.grad.lerp(buf, g["momentum"]) if g["nesterov"] else buf
                u = zeropower(u, g["ns_steps"])
                p.add_(u, alpha=-g["lr"] * max(1.0, p.size(0) / p.size(1)) ** 0.5)
