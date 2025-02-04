import torch
import torch.nn as nn
import matplotlib.pyplot as plt

class ARX(nn.Module):
    def __init__(self, regressor_dim, sequence_length, ar_order, exogenous_dim):
        super(ARX, self).__init__()

        self.regressor_dim = regressor_dim
        self.sequence_length = sequence_length
        self.ar_order = ar_order
        self.exogenous_dim = exogenous_dim
        # Create single linear layer
        self.linear = nn.Linear(self.regressor_dim, 1, bias=False)

    def forward(self, y, u):
        batch_size = y.size(0)
        device = y.device 
        
        # Initialize the output
        output = torch.zeros(batch_size, self.sequence_length+self.ar_order+1).to(y.device)

        # Start by filling in the initial conditions for the output
        output[:, :self.ar_order+1] = y

        for t in range(self.ar_order+1, self.sequence_length+self.ar_order+1):
            # Use the most recent output values and exogenous variables as the regressor
            #regressor = torch.cat((output[:, (t-self.ar_order):t], u[:,t-self.ar_order].unsqueeze(1)), dim=1)
            regressor = torch.cat((output[:, (t-self.ar_order):(t)] - output[:, (t-self.ar_order-1):(t-1)],
                                    u[:,(t-self.ar_order):(t-self.ar_order+self.exogenous_dim)]), dim=1)
            # Compute the prediction
            prediction_t = self.linear(regressor)
    
            # Store the prediction in the output tensor
            output[:, t] = output[:, t-1] + prediction_t.squeeze()

        return output

