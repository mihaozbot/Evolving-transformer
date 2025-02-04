
from numpy.linalg import inv
import torch
import torch.nn as nn

class EvolvingSystem(nn.Module):
    def __init__(self, batch_size, input_length, output_dim, output_length,  num_clusters, latent_dim, regressor_dim,min_clamp,max_clamp):
        super(EvolvingSystem, self).__init__()
        self.input_length = input_length
        self.output_dim = output_dim
        self.output_length = output_length
        self.cluster_dim = latent_dim
        self.num_clusters = num_clusters
        self.regressor_dim = regressor_dim
        self.min_clamp = min_clamp
        self.max_clamp = max_clamp
        self.batch_size = batch_size
        #self.etta = torch.nn.Parameter(data=torch.ones(1), requires_grad=True)
        self.mu = torch.nn.Parameter(data = 1*torch.rand(self.num_clusters,self.cluster_dim), requires_grad=True)
        #self.sigma_inv = torch.nn.Parameter(data=(0.1*torch.rand(self.num_clusters,self.cluster_dim, self.cluster_dim)  + 
        #    	torch.diag_embed(1*torch.ones(self.num_clusters,self.cluster_dim),dim=2)), requires_grad=True)
        #self.sigma_inv = torch.nn.Parameter(data=(torch.diag_embed(1*torch.ones(self.num_clusters,self.cluster_dim))), requires_grad=True)# torch.nn.Parameter(data=(0.1*torch.rand(self.num_clusters,self.cluster_dim, self.cluster_dim)), requires_grad=True)
        self.sigma_inv = nn.Parameter(torch.zeros(self.num_clusters, self.cluster_dim, self.cluster_dim), requires_grad=True)
        with torch.no_grad():
            self.sigma_inv.diagonal(dim1=-2, dim2=-1).fill_(10)
        #self.sigma_inv = torch.nn.Parameter(data=10*torch.rand(self.num_clusters,self.cluster_dim, self.cluster_dim), requires_grad=True)
        #self.sigma = torch.nn.Parameter(torch.matmul(self.sigma_inv, torch.transpose(self.sigma_inv, 2, 1)), requires_grad=True)
        #self.sigma_alpha = torch.nn.Parameter(data=torch.randn(self.num_clusters,self.cluster_dim), requires_grad=True)
        
        #self.fc_con = nn.Linear(input_length, output_length) #output_length
        #self.fc_con = nn.Linear(self.regressor_dim+1, self.num_clusters*self.output_dim, bias=False) #output_length
        #self.fc_recon = nn.Linear(self.regressor_dim+1, self.num_clusters*self.input_length, bias=False) #output_length
        
                # Create separate linear layers for fc_con and fc_recon
        self.fc_con_layers = nn.ModuleList([
            nn.Linear(self.regressor_dim + 1, self.output_length, bias=False)
            for _ in range(self.num_clusters)
        ])
        
        self.fc_recon_layers = nn.ModuleList([
            nn.Linear(self.regressor_dim +1, self.input_length, bias=False)
            for _ in range(self.num_clusters)
        ])
        
        #self.fc_recon = nn.Linear(self.num_clusters*regressor_dim,  self.num_clusters*regressor_dim) #output_length
        #self.fc_con = FeedForward(input_length, self.num_clusters, 20) #output_length
        #self.fc_recon = FeedForward(input_length, input_length*self.num_clusters, 1)
        #self.fc_con = FeedForward(input_length, self.num_clusters, input_length) #output_length
        #self.fc_recon = FeedForward(input_length, input_length*self.num_clusters, input_length)
        self.sm = torch.nn.Softmax(dim = 1)
        self.ones = nn.Parameter(torch.ones((self.batch_size, 1, 1)), requires_grad=False)
        
    def softmax(x):
        # Ensure numerical stability by subtracting the maximum value
        max_val, _ = torch.max(x, dim=1, keepdim=True)
        x_exp = torch.exp(x - max_val)
        
        # Compute the softmax probabilities
        softmax_probs = x_exp / torch.sum(x_exp, dim=1, keepdim=True)
    
        return softmax_probs

        #self.evol_drop_layer = nn.Dropout(p=0.5)
    def add_new_rule(self, z):
        print('TODO')
        
    def compute_centers(self, z):
        psi = self.compute_psi(z)

        mu = torch.sum(torch.einsum('bmi, bmj->bji', psi, z),0)
        mu /= psi.sum(dim=0).clamp_min_(1e-12)
        
        return mu

    
    def compute_psi(self, z):
        
        d = torch.sub((self.mu), z)
        dl = d.reshape(self.batch_size, self.num_clusters, 1, self.cluster_dim)
        
        #TEST OK -> self.mu-self.x_ant[0][0], d[0], dl[0]
        sigma_inv = torch.matmul((self.sigma_inv), torch.transpose((self.sigma_inv), 2, 1))

        d2_dS = torch.matmul(dl, sigma_inv)

        dr = d.reshape(self.batch_size, self.num_clusters, self.cluster_dim, 1)

        #d2 = torch.matmul(d2_dS, dr)
        d2 = torch.clamp( torch.matmul(d2_dS, dr), min=self.min_clamp)
        #d2 = torch.pow(d2, torch.pow(self.etta, 2)
        psi = self.sm(-d2.reshape(self.batch_size, self.num_clusters,1))
        #psi = self.evol_drop_layer(psi)
        #TEST OK -> self.sm(-d2).reshape(self.batch_size,1,self.num_clusters)[0], self.sm(-d2)
        psi = psi.reshape(self.batch_size, 1, self.num_clusters)
        return psi

    def compute_psi_detached(self, z):
        
        mu = self.mu.detach()
        sigma_inv = self.sigma_inv.detach()

        d = torch.sub((mu), z)
        dl = d.reshape(self.batch_size, self.num_clusters, 1, self.cluster_dim)
        
        #TEST OK -> self.mu-self.x_ant[0][0], d[0], dl[0]
        sigma_inv = torch.matmul((sigma_inv), torch.transpose((sigma_inv), 2, 1))

        d2_dS = torch.matmul(dl, sigma_inv)

        dr = d.reshape(self.batch_size, self.num_clusters, self.cluster_dim, 1)

        #d2 = torch.matmul(d2_dS, dr)
        d2 = torch.clamp( torch.matmul(d2_dS, dr), min=self.min_clamp)
        #d2 = torch.pow(d2, torch.pow(self.etta, 2)
        psi = self.sm(-d2.reshape(self.batch_size, self.num_clusters,1))
        #psi = self.evol_drop_layer(psi)
        #TEST OK -> self.sm(-d2).reshape(self.batch_size,1,self.num_clusters)[0], self.sm(-d2)
        psi = psi.reshape(self.batch_size, 1, self.num_clusters)
        return psi
    
    '''
    def forward(self, z, x):

        x  = torch.cat((x, self.ones), dim=2)  
        #self.x_ant = torch.cat((self.x_ant, u.reshape(self.batch_size,1,1)), dim = 2)
        self.psi = self.compute_psi(z)

        #x_con = x_con.repeat(1,self.num_clusters,1)
        self.y_LLM  = torch.abs(self.fc_con(x)) #.reshape(self.batch_size, -1, self.num_clusters) #.reshape(self.batch_size, output_length, self.num_clusters)
        y_con = torch.matmul(self.psi, torch.transpose( self.y_LLM ,-1,-2))

        #x_recon = torch.zeros(self.batch_size, self.num_clusters, input_length, regressor_dim).to(device)
        #x_recon[:,:,0,:] = x.repeat(1,self.num_clusters,1)
        #for step in range(1,input_length):
        #        x_recon[:,:,step,:] = self.fc_recon(x_recon[:,:,step-1,:].reshape(self.batch_size, self.num_clusters*regressor_dim)).reshape(self.batch_size, self.num_clusters, regressor_dim)
        #x_recon = torch.matmul(self.psi, x_recon[:,:,:,1])

        self.x_LLM = torch.abs(self.fc_recon(x)).reshape(self.batch_size, self.num_clusters, self.input_length)
        x_recon = torch.matmul(self.psi, self.x_LLM)
        
        #print(torch.sum(psi[0]))
        #y = torch.transpose(y_con,-1,-2) #torch.matmul(self.psi, torch.transpose(y_con,-1,-2))
        #self.x_recon = torch.matmul(self.psi, torch.transpose(x_recon,1,0).reshape(input_length,self.batch_size,self.num_clusters, 1)).reshape(self.batch_size, 1, input_length)
        
        #final_out = self.fc(out)
        return y_con, x_recon
    '''
    def forward(self, z, u, member):
        device = z.device 
        self.psi = self.compute_psi(z)  # Move z to the same device as self.psi

        y_con_i = []
        x_recon_i = []
        self.x_LLM = []
        self.y_LLM = []

        for i in range(self.num_clusters):
            fc_con_layer = self.fc_con_layers[i].to(device)
            fc_recon_layer = self.fc_recon_layers[i].to(device)

            #self.y_LLM.append(torch.abs(fc_con_layer(u[:,:,1:])*u[:,:,0].unsqueeze(1)).squeeze())
            self.y_LLM.append(torch.abs(fc_con_layer(u)).squeeze())
            y_con_i.append(self.psi[:, :, i] * self.y_LLM[i])

            #self.x_LLM.append(torch.abs(fc_recon_layer(u[:,:,1:])*u[:,:,0].unsqueeze(1)).squeeze())
            self.x_LLM.append(torch.abs(fc_recon_layer(u)).squeeze())
            x_recon_i.append(member[:, :, i] * self.x_LLM[i])

        y_con = torch.stack(y_con_i, dim=1).sum(dim=1).unsqueeze(1)
        x_recon = torch.stack(x_recon_i, dim=1).sum(dim=1).unsqueeze(1)

        self.x_LLM = torch.stack(self.x_LLM, dim=1)
        self.y_LLM = torch.stack(self.y_LLM, dim=1)

        return y_con, x_recon
