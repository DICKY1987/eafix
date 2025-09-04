import React, { useState, useEffect } from 'react';
import { 
  Workflow, 
  Play, 
  Square, 
  Settings, 
  FileText, 
  BarChart3, 
  GitBranch,
  Plus,
  Edit3,
  Trash2,
  Download,
  Upload,
  Eye,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Database,
  Code,
  Zap
} from 'lucide-react';

const AtomicProcessGUI = () => {
  const [activeTab, setActiveTab] = useState('processes');
  const [processFlow, setProcessFlow] = useState(null);
  const [subProcesses, setSubProcesses] = useState([]);
  const [analysisData, setAnalysisData] = useState(null);
  const [syncStatus, setSyncStatus] = useState('synced');
  const [selectedStep, setSelectedStep] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Mock data - in real implementation, this would come from your Python backend
  const mockProcessFlow = {
    title: "Trading System Process",
    version: "1.0.0",
    sections: [
      {
        section_id: "1.000",
        title: "Order Processing",
        description: "Main order processing workflow",
        actors: ["TRADER", "SYSTEM", "RISK_ENGINE"],
        transport: "HTTP/AMQP",
        steps: [
          {
            step_id: "1.001",
            actor: "TRADER",
            description: "Submit order request",
            sla_ms: 100,
            input_variables: ["order_data"],
            output_variables: ["order_id", "timestamp"],
            subprocess_calls: []
          },
          {
            step_id: "1.002", 
            actor: "SYSTEM",
            description: "Validate order parameters",
            sla_ms: 50,
            input_variables: ["order_id", "order_data"],
            output_variables: ["validation_result"],
            subprocess_calls: [
              {
                subprocess_id: "VALIDATE_ORDER",
                description: "Order validation sub-process"
              }
            ]
          },
          {
            step_id: "1.003",
            actor: "RISK_ENGINE", 
            description: "Perform risk assessment",
            sla_ms: 200,
            input_variables: ["order_data", "validation_result"],
            output_variables: ["risk_score", "approval_status"],
            subprocess_calls: []
          }
        ]
      }
    ]
  };

  const mockSubProcesses = [
    {
      subprocess_id: "VALIDATE_ORDER",
      name: "Order Validation",
      description: "Comprehensive order validation process",
      inputs: [
        { name: "order_data", data_type: "object", required: true },
        { name: "market_data", data_type: "object", required: false }
      ],
      outputs: [
        { name: "is_valid", data_type: "boolean", required: true },
        { name: "validation_errors", data_type: "array", required: false }
      ]
    },
    {
      subprocess_id: "RISK_ASSESSMENT",
      name: "Risk Assessment",
      description: "Real-time risk analysis",
      inputs: [
        { name: "portfolio", data_type: "object", required: true },
        { name: "order_amount", data_type: "number", required: true }
      ],
      outputs: [
        { name: "risk_score", data_type: "number", required: true },
        { name: "risk_factors", data_type: "array", required: false }
      ]
    }
  ];

  const mockAnalysis = {
    performance_metrics: {
      total_estimated_time_ms: 350,
      critical_path_time_ms: 250,
      bottleneck_steps: ["1.003"]
    },
    complexity_metrics: {
      cyclomatic_complexity: 8,
      maintainability_score: 7.5
    },
    quality_metrics: {
      documentation_completeness: 85,
      error_handling_coverage: 70
    }
  };

  useEffect(() => {
    // Simulate loading data
    setProcessFlow(mockProcessFlow);
    setSubProcesses(mockSubProcesses);
    setAnalysisData(mockAnalysis);
  }, []);

  const handleStepClick = (step) => {
    setSelectedStep(step);
  };

  const handleSync = async () => {
    setIsLoading(true);
    setSyncStatus('syncing');
    
    // Simulate sync operation
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setSyncStatus('synced');
    setIsLoading(false);
  };

  const getSyncStatusIcon = () => {
    switch(syncStatus) {
      case 'synced': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'syncing': return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const StepCard = ({ step, onClick }) => (
    <div 
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onClick(step)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-mono text-blue-600">{step.step_id}</span>
            <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{step.actor}</span>
            {step.sla_ms && (
              <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded">
                {step.sla_ms}ms SLA
              </span>
            )}
          </div>
          <p className="text-gray-900 font-medium mb-2">{step.description}</p>
          
          {step.subprocess_calls && step.subprocess_calls.length > 0 && (
            <div className="flex items-center gap-1 text-sm text-purple-600 mb-2">
              <GitBranch className="w-4 h-4" />
              <span>{step.subprocess_calls.length} sub-process(es)</span>
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            {step.input_variables && step.input_variables.length > 0 && (
              <div>
                <span className="text-gray-500">Inputs:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {step.input_variables.map((input, idx) => (
                    <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                      {input}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {step.output_variables && step.output_variables.length > 0 && (
              <div>
                <span className="text-gray-500">Outputs:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {step.output_variables.map((output, idx) => (
                    <span key={idx} className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded">
                      {output}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex gap-2">
          <button className="p-1 hover:bg-gray-100 rounded">
            <Edit3 className="w-4 h-4 text-gray-500" />
          </button>
          <button className="p-1 hover:bg-gray-100 rounded">
            <Trash2 className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>
    </div>
  );

  const ProcessView = () => (
    <div className="space-y-6">
      {processFlow?.sections.map((section) => (
        <div key={section.section_id} className="bg-gray-50 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
              <p className="text-gray-600">{section.description}</p>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  <span>{section.actors.join(', ')}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Database className="w-4 h-4" />
                  <span>{section.transport}</span>
                </div>
              </div>
            </div>
            <button className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Plus className="w-4 h-4" />
              Add Step
            </button>
          </div>
          
          <div className="space-y-3">
            {section.steps.map((step) => (
              <StepCard key={step.step_id} step={step} onClick={handleStepClick} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  const SubProcessView = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Sub-Processes</h2>
        <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
          <Plus className="w-4 h-4" />
          New Sub-Process
        </button>
      </div>
      
      <div className="grid gap-4">
        {subProcesses.map((subprocess) => (
          <div key={subprocess.subprocess_id} className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{subprocess.name}</h3>
                <p className="text-sm font-mono text-purple-600 mb-2">{subprocess.subprocess_id}</p>
                <p className="text-gray-600">{subprocess.description}</p>
              </div>
              
              <div className="flex gap-2">
                <button className="p-2 hover:bg-gray-100 rounded">
                  <Edit3 className="w-4 h-4 text-gray-500" />
                </button>
                <button className="p-2 hover:bg-gray-100 rounded">
                  <Eye className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Inputs</h4>
                <div className="space-y-2">
                  {subprocess.inputs.map((input, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                      <span className="font-medium text-blue-900">{input.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-blue-600">{input.data_type}</span>
                        {input.required && <span className="text-xs text-red-500">required</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Outputs</h4>
                <div className="space-y-2">
                  {subprocess.outputs.map((output, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="font-medium text-green-900">{output.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-green-600">{output.data_type}</span>
                        {output.required && <span className="text-xs text-red-500">required</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const AnalysisView = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Total Time</span>
              <span className="font-mono">{analysisData?.performance_metrics.total_estimated_time_ms}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Critical Path</span>
              <span className="font-mono">{analysisData?.performance_metrics.critical_path_time_ms}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Bottlenecks</span>
              <span className="text-red-600">{analysisData?.performance_metrics.bottleneck_steps.length}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Complexity</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Cyclomatic</span>
              <span className="font-mono">{analysisData?.complexity_metrics.cyclomatic_complexity}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Maintainability</span>
              <span className="font-mono">{analysisData?.complexity_metrics.maintainability_score}/10</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Documentation</span>
              <span className="font-mono">{analysisData?.quality_metrics.documentation_completeness}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Error Handling</span>
              <span className="font-mono">{analysisData?.quality_metrics.error_handling_coverage}%</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization Recommendations</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <p className="font-medium text-yellow-900">Performance Bottleneck</p>
              <p className="text-yellow-800">Step 1.003 (Risk Assessment) has high SLA time. Consider optimizing or parallelizing.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded">
            <Zap className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <p className="font-medium text-blue-900">Sub-Process Opportunity</p>
              <p className="text-blue-800">Consider extracting repeated validation logic into reusable sub-processes.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Workflow className="w-8 h-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Atomic Process Framework</h1>
            </div>
            
            <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-lg">
              {getSyncStatusIcon()}
              <span className="text-sm text-gray-600 capitalize">{syncStatus}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={handleSync}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Sync
            </button>
            
            <button className="flex items-center gap-2 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
              <Download className="w-4 h-4" />
              Export
            </button>
            
            <button className="flex items-center gap-2 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white border-r border-gray-200 h-screen overflow-y-auto">
          <div className="p-4 space-y-2">
            <button
              onClick={() => setActiveTab('processes')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left ${
                activeTab === 'processes' ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Workflow className="w-5 h-5" />
              Process Flows
            </button>
            
            <button
              onClick={() => setActiveTab('subprocesses')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left ${
                activeTab === 'subprocesses' ? 'bg-purple-100 text-purple-700' : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <GitBranch className="w-5 h-5" />
              Sub-Processes
            </button>
            
            <button
              onClick={() => setActiveTab('analysis')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left ${
                activeTab === 'analysis' ? 'bg-green-100 text-green-700' : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              Analysis
            </button>
            
            <button
              onClick={() => setActiveTab('docs')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left ${
                activeTab === 'docs' ? 'bg-yellow-100 text-yellow-700' : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <FileText className="w-5 h-5" />
              Documentation
            </button>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {activeTab === 'processes' && <ProcessView />}
          {activeTab === 'subprocesses' && <SubProcessView />}
          {activeTab === 'analysis' && <AnalysisView />}
          {activeTab === 'docs' && (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Documentation Center</h3>
              <p className="text-gray-600">Generate and view synchronized documentation formats</p>
            </div>
          )}
        </main>
      </div>

      {/* Step Detail Modal */}
      {selectedStep && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Step Details</h2>
                <button 
                  onClick={() => setSelectedStep(null)}
                  className="p-2 hover:bg-gray-100 rounded"
                >
                  <Square className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Step ID</label>
                <input 
                  type="text" 
                  value={selectedStep.step_id} 
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  readOnly
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea 
                  value={selectedStep.description} 
                  className="w-full p-2 border border-gray-300 rounded-lg h-20"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Actor</label>
                  <select className="w-full p-2 border border-gray-300 rounded-lg">
                    <option value={selectedStep.actor}>{selectedStep.actor}</option>
                    <option value="TRADER">TRADER</option>
                    <option value="SYSTEM">SYSTEM</option>
                    <option value="RISK_ENGINE">RISK_ENGINE</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">SLA (ms)</label>
                  <input 
                    type="number" 
                    value={selectedStep.sla_ms || ''} 
                    className="w-full p-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
                <button 
                  onClick={() => setSelectedStep(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AtomicProcessGUI;