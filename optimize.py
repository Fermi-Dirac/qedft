#import input
import os
import numpy
import time
import copy
import config


ry2ev = 13.605693
bohr2ang = 0.529177

def latticeConstant(io, low, high, steps, optParams):
	"""optimize lattice constant by """
	subDir = 'lattice-op'
	opDir = os.path.join(io.workingDir, subDir)
	if not optParams.replot:
		if optParams.restart: 
			if not os.path.isdir(opDir):
				io.log('You are attempting to restart a calculation, but the previous results were not found. Set restart=False to start a new calculation.')
				return
			io.restart = True
		else:
			io.clearDir(subDir)
		latticeConstants = numpy.linspace(low, high, steps)
		io.log('Lattice calculation commenced %s (server time)' % time.asctime())
		io.startingwfc = optParams.startingwfc
		io.startingpot = optParams.startingpot
		for a in latticeConstants:
			low = a #Necessary in case optimization must be restarted
			steps += -1 #Necessary in case optimization must be restarted
			io.optimization = 'lattice'
			io.optLocals = locals()
			io.a = a/bohr2ang
			io.write()
			opFilename = opDir+'/lattice-%f' % a
			io.runPw(opFilename)
			#io.startingpot = 'file'
			#io.startingwfc = 'file'
			data = io.parseResults('lattice-op', log='lattice')
			data = sorted(data, key=lambda k: float(k['latticeConstant']))
			pt = data[-1]
			io.log('E(%s) = %s' % (pt['latticeConstant'], pt['energy']))
			io.log('Iteration wall time: %is' % pt['wallTime'])
			io.log('Date/Time: %s' % data[-1]['dateTime'])
		io.parseResults(subDir, log='lattice')
	if os.path.isdir(opDir):
		returnDict = io.fitLattice(plot=optParams.plot, subDir='lattice-op')
		if returnDict:
			io.log("Quadratic data fit yields a lattice constant of %f" % returnDict['quadFit'])
			io.log("Birch-Murnaghan EOS fit yields a lattice constant of %f" % returnDict['BMfit'])
			if optParams.plot and config.system.hasDisplay:
				raw_input('Press any key to continue')
		else:
			io.log('Lattice calculation complete.')
		if optParams.email or optParams.text:
			message = '%s calculation complete on project: %s' % ('lattice', io.project)
			files = returnDict['files'] or False
			io.report(message, text=text, email=email, files=files)
	else:
		io.log("Directory lattice-op not found. Is replot set to True without first running caluclations with replot=False?")
		
def cutWfc(io, low, high, stepsize, optParams, rhoRatio = 4):
	qeParam = 'ecutwfc'
	cutoffs(**locals())

def cutRho(io, low, high, stepsize, optParams):
	qeParam = 'ecutrho'
	cutoffs(**locals())	

def cutoffs(io, low, high, stepsize, qeParam, optParams, rhoRatio = 4):
	subDir = qeParam+'-op'
	opDir =  os.path.join(io.workingDir, subDir)
	if optParams.replot:
		if os.path.isdir(opDir):
			returnDict = io.fitCutoff(qeParam, subDir)
			message = '%s calculation complete on project: %s' % (qeParam, io.project)
			io.report(message, text=optParams.text, email=optParams.email, files=returnDict['files'])
			return
	if optParams.restart: 
		if not os.path.isdir(opDir):
			io.log('You are attempting to restart a calculation, but the previous results were not found. Set restart=False to start a new calculation.')
			return
		#io.restart = True
	else:
		io.clearDir(subDir)
	io.startingwfc = optParams.startingwfc
	io.startingpot = optParams.startingpot
	testE = low
	triggered = False
	converged = False
	if optParams.convEV == 'auto':
		optParams.convEV = io.nat * 0.001
	io.log('%s calculation commenced %s (server time)' % (qeParam, time.asctime()))
	while testE <= high:
		io.optimization = qeParam
		io.optLocals = locals()
		opFilename = opDir+'/%s-%f' % (qeParam, testE)
		if qeParam == 'ecutwfc':
			io.eCutWfc = testE
			if rhoRatio:
				io.eCutRho = rhoRatio*testE
		if qeParam == 'ecutrho':
			io.eCutRho = testE
		io.write()
		io.runPw(opFilename)
		#io.startingwfc = 'file'
		#io.startingpot = 'file'
		data = io.parseResults(subDir)
		data = sorted(data, key=lambda k: float(k[qeParam]))
		io.log('Total energy for %s=%i: %f' % (qeParam, testE, data[-1]['energy']))
		io.log('Total time: %is' % data[-1]['wallTime'])
		io.log('Date/time: %s' % data[-1]['dateTime'])
		if testE > low:
			delta = data[-1]['energy'] - data[-2]['energy']
			deltaEV = delta*ry2ev
			io.log('%f eV change' % deltaEV)
			if abs(deltaEV) < optParams.convEV:
				if triggered:
					io.eCutWfc = testE
					io.log('%s converged at %i' % (qeParam, testE))
					converged = True
					break
				else:
					triggered = True
		testE += stepsize
	io.parseResults(subDir, log=qeParam)
	if not converged:
		io.log('%s did not converge' % qeParam)
	if optParams.plot:
		returnDict = io.fitCutoff(qeParam, subDir)
		if optParams.email or optParams.text:
			if not returnDict:
				message = '%s calculation on %s project completed after fewer than 5 iterations' % (qeParam, io.project)
				io.report(message, text=optParams.text, email=optParams.email)
			else:
				message = '%s calculation complete on project: %s' % (qeParam, io.project)
				io.report(message, text=optParams.text, email=optParams.email, files=returnDict['files'])

def kGrid(io, startGrid, steps, optParams, stepsize = [2,2,2]):
	io.kConverged = False
	subDir = 'kgrid-op'
	opDir = os.path.join(io.workingDir, subDir)
	if optParams.replot:
		returnDict = io.fitKgrid(subDir)
		message = '%s calculation complete on project: %s' % ('k-grid', io.project)
		io.report(message, text=optParams.text, email=optParams.email, files=returnDict['files'])
		return
	if optParams.restart: 
		if not os.path.isdir(opDir):
			io.log('You are attempting to restart a calculation, but the previous results were not found. Set restart=False to start a new calculation.')
			return
		io.restart = True
	else:
		io.clearDir(subDir)
	trigger = []
	triggered = False
	converged = False
	io.kxyz = startGrid
	io.startingwfc = optParams.startingwfc
	io.startingpot = optParams.startingpot
	if optParams.convEV == 'auto':
		optParams.convEV = io.nat * 0.001
	io.log('k-grid calculation commenced %s (server time)' % time.asctime())
	i = 0
	while i < steps:
		io.optimization = 'kgrid'
		io.optLocals = locals()
		opFilename = opDir+'/kgrid-%i-%i-%i' % (io.kxyz[0], io.kxyz[1], io.kxyz[2]) 
		io.write()
		io.runPw(opFilename)
		#io.startingwfc = 'file'
		#io.startingpot = 'file'
		data = io.parseResults('kgrid-op')
		data = sorted(data, key=lambda k: float(float(k['kGridDict']['x']) + float(k['kGridDict']['y']) + float(k['kGridDict']['z'])))
		io.log('Total energy for %s k-points: %f' % (str(data[-1]['kGridDict']), data[-1]['energy']))
		io.log('Total time: %is' % data[-1]['wallTime'])
		io.log('Date/time: %s' % data[-1]['dateTime'])
		if i > 0:
			delta = data[-1]['energy'] - data[-2]['energy']
			deltaEV = delta*ry2ev
			io.log(str(deltaEV)+'eV change')
			if abs(deltaEV) < optParams.convEV:
				if triggered:
					io.kxyz = trigger
					io.log('k divisions converged at '+str(io.kxyz))
					converged = True
					break
				else:
					triggered = True
					trigger = copy.copy(io.kxyz)
		io.kxyz = [io.kxyz[0] + stepsize[0], io.kxyz[1] + stepsize[1], io.kxyz[2] + stepsize[2]]
		i += 1
	io.parseResults('kgrid-op', log='kGrid')
	if optParams.plot:
		returnDict = io.fitKgrid(subDir)
		if optParams.email or optParams.text:
			message = '%s calculation complete on project: %s' % ('k-grid', io.project)
			io.report(message, text=optParams.text, email=optParams.email, files=returnDict['files'])
	if not converged:
		io.log('k grid did not converge')
	
def relax(io, nstep, optParams, constraints = False, vc=False):
	io.nstep = nstep
	calcType = 'vc-relax' if vc else 'relax'
	subDir = 'vc-relax-op' if vc else 'relax-op'
	io.constraints = constraints
	io.calculation = calcType
	io.startingwfc = optParams.startingwfc
	io.startingpot = optParams.startingpot
	io.write()
	opDir = os.path.join(io.workingDir,subDir)
	opFilename = os.path.join(opDir,calcType)
	if not optParams.replot:
		io.optimization = 'relax'
		io.optLocals = locals()
		io.log('Relaxation calculation commenced %s (server time)' % time.asctime())
		if optParams.restart: 
			if not os.path.isdir(opDir):
				io.log('You are attempting to restart a calculation, but the previous results were not found. Set restart=False to start a new calculation.')
				return
			io.restart = True
		else:
			io.clearDir(subDir)
		io.runPw(opFilename)
		io.parseResults(subDir, log=calcType)
	io.constraints = False
	io.calculation = 'scf'
	if optParams.email or optParams.text:
		message = '%s calculation complete on project: %s' % ('relaxation', io.project)
		io.report(message, text=optParams.text, email=optParams.email)
	
def quickRun(io, optParams):
	subDir = 'quickrun-op'
	io.clearDir(subDir)
	opFilename = os.path.join(io.workingDir,subDir,'quickrun')
	io.startingpot = optParams.startingpot
	io.startingwfc = optParams.startingwfc
	io.write()
	io.log('Calculation commenced %s (server time)' % time.asctime())
	io.runPw(opFilename)
	data = io.parseResults(subDir, log='quick-run')[0]
	io.log('Success!\n Total Energy: %f \n Wall time: %is \n CPU time: %is' % (data['energy'], data['wallTime'], data['cpuTime']))
	message = '%s calculation complete on project: %s' % ('single quick-run', io.project)
	io.report(message, text=optParams.text, email=optParams.email)
		
	

		