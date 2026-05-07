import React from 'react';

export default function AlgorithmInsights({ interactionCount, strategy }) {
  const derivedAlgo =
    strategy ||
    (interactionCount == null
      ? 'none'
      : interactionCount <= 5
        ? 'demographic'
        : interactionCount < 20
        ? 'content'
        : interactionCount <= 70
          ? 'svd'
          : 'collaborative');

  let activeAlgo = derivedAlgo;
  let statusText = 'Awaiting User Selection';
  let statusColor = 'bg-gray-100 text-gray-600';

  if (interactionCount !== null || strategy) {
    if (activeAlgo === 'demographic') {
      statusText = 'Backend Strategy: Demographic Cold Start';
      statusColor = 'bg-amber-100 text-amber-700';
    } else
    if (activeAlgo === 'content') {
      statusText = 'Backend Strategy: Content-Based (Cold Start)';
      statusColor = 'bg-blue-100 text-blue-700';
    } else if (activeAlgo === 'svd') {
      statusText = 'Backend Strategy: SVD Matrix Factorization';
      statusColor = 'bg-purple-100 text-purple-700';
    } else if (activeAlgo === 'collaborative') {
      statusText = 'Backend Strategy: Collaborative Filtering';
      statusColor = 'bg-teal-100 text-teal-700';
    }
  }

  const getRowClass = (algo) => {
    const baseClass = "transition-all duration-200 ";
    if (algo === activeAlgo) {
      return baseClass + "bg-indigo-50 border-l-4 border-indigo-500 shadow-sm";
    }
    return baseClass + "bg-white/40 hover:bg-white/60 border-l-4 border-transparent";
  };

  const getCellClass = (algo, isNumeric = false) => {
    let cls = isNumeric ? "px-4 py-3 text-right " : "px-4 py-3 font-medium ";
    if (algo === activeAlgo) {
      cls += isNumeric ? "text-indigo-700 font-semibold" : "text-indigo-900";
    } else {
      cls += isNumeric ? "text-gray-500" : "text-gray-800";
    }
    return cls;
  };

  return (
    <div className="glass-card p-6 mt-6">
      <div className="flex items-center justify-between border-b border-gray-200 pb-2 mb-4">
        <h2 className="text-xl font-bold text-gray-800">Algorithm Insights</h2>
        {interactionCount !== null && (
          <span className="text-xs font-semibold px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full">
            {interactionCount} Interactions Found
          </span>
        )}
      </div>
      
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-md font-semibold text-indigo-600">Active Pipeline Logic</h3>
            {interactionCount !== null && (
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${statusColor}`}>
                {statusText}
              </span>
            )}
          </div>
          
          <ul className="space-y-4 text-sm mt-4">
            <li className={`flex items-start p-3 rounded-lg border ${activeAlgo === 'demographic' ? 'bg-amber-50/50 border-amber-200' : 'border-transparent opacity-60'}`}>
              <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mr-3 mt-0.5 font-bold ${activeAlgo === 'demographic' ? 'bg-amber-100 text-amber-600' : 'bg-gray-100 text-gray-500'}`}>1</span>
              <div>
                <strong className={`block ${activeAlgo === 'demographic' ? 'text-amber-900' : 'text-gray-700'}`}>Demographic Cold Start</strong>
                <span className="text-gray-600 block mt-1"><strong>Reason:</strong> Backend selects this when the user has 0-5 interactions.</span>
                <span className="text-gray-600 block"><strong>Action:</strong> Uses age, gender, and occupation to find similar users.</span>
              </div>
            </li>

            <li className={`flex items-start p-3 rounded-lg border ${activeAlgo === 'content' ? 'bg-blue-50/50 border-blue-200' : 'border-transparent opacity-60'}`}>
              <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mr-3 mt-0.5 font-bold ${activeAlgo === 'content' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>2</span>
              <div>
                <strong className={`block ${activeAlgo === 'content' ? 'text-blue-900' : 'text-gray-700'}`}>Content-Based Filtering (Genres)</strong>
                <span className="text-gray-600 block mt-1"><strong>Reason:</strong> Backend selects this when the user has 6-19 interactions.</span>
                <span className="text-gray-600 block"><strong>Action:</strong> Uses TF-IDF on genre similarity to handle sparse history.</span>
              </div>
            </li>

            <li className={`flex items-start p-3 rounded-lg border ${activeAlgo === 'svd' ? 'bg-purple-50/50 border-purple-200' : 'border-transparent opacity-60'}`}>
              <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mr-3 mt-0.5 font-bold ${activeAlgo === 'svd' ? 'bg-purple-100 text-purple-600' : 'bg-gray-100 text-gray-500'}`}>3</span>
              <div>
                <strong className={`block ${activeAlgo === 'svd' ? 'text-purple-900' : 'text-gray-700'}`}>Matrix Factorization (TruncatedSVD)</strong>
                <span className="text-gray-600 block mt-1"><strong>Reason:</strong> Backend selects this for users with 20-69 interactions.</span>
                <span className="text-gray-600 block"><strong>Action:</strong> Discovers hidden preference patterns and latent factors.</span>
              </div>
            </li>

            <li className={`flex items-start p-3 rounded-lg border ${activeAlgo === 'collaborative' ? 'bg-teal-50/50 border-teal-200' : 'border-transparent opacity-60'}`}>
              <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mr-3 mt-0.5 font-bold ${activeAlgo === 'collaborative' ? 'bg-teal-100 text-teal-600' : 'bg-gray-100 text-gray-500'}`}>4</span>
              <div>
                <strong className={`block ${activeAlgo === 'collaborative' ? 'text-teal-900' : 'text-gray-700'}`}>Collaborative Filtering (Cosine)</strong>
                <span className="text-gray-600 block mt-1"><strong>Reason:</strong> Backend selects this when the user has 70 or more interactions.</span>
                <span className="text-gray-600 block"><strong>Action:</strong> Leverages exact user similarity to reliably find "people like you".</span>
              </div>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-md font-semibold text-indigo-600 mb-3">Model Performance Matrix</h3>
          <p className="text-sm text-gray-500 mb-4">
            Comparison of recommendation models. The highlighted row indicates the algorithm currently serving recommendations for the selected user.
          </p>
          <div className="overflow-x-auto rounded-lg border border-gray-100 shadow-sm">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50/80 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3 font-medium">Model</th>
                  <th className="px-4 py-3 font-medium text-right">RMSE</th>
                  <th className="px-4 py-3 font-medium text-right">MAE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr className={getRowClass('demographic')}>
                  <td className={getCellClass('demographic')}>Demographic Cold Start</td>
                  <td className={getCellClass('demographic', true)}>N/A</td>
                  <td className={getCellClass('demographic', true)}>N/A</td>
                </tr>
                <tr className={getRowClass('content')}>
                  <td className={getCellClass('content')}>Content-Based (TF-IDF)</td>
                  <td className={getCellClass('content', true)}>0.924</td>
                  <td className={getCellClass('content', true)}>0.741</td>
                </tr>
                <tr className={getRowClass('svd')}>
                  <td className={getCellClass('svd')}>Hybrid (TruncatedSVD)</td>
                  <td className={getCellClass('svd', true)}>0.835</td>
                  <td className={getCellClass('svd', true)}>0.658</td>
                </tr>
                <tr className={getRowClass('collaborative')}>
                  <td className={getCellClass('collaborative')}>Collaborative (Cosine KNN)</td>
                  <td className={getCellClass('collaborative', true)}>0.891</td>
                  <td className={getCellClass('collaborative', true)}>0.702</td>
                </tr>
              </tbody>
            </table>
          </div>
          {interactionCount === null && (
            <div className="mt-4 p-3 bg-amber-50 text-amber-700 text-sm rounded-lg border border-amber-100 flex items-center gap-2">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Select a user to see which algorithm powers their recommendations.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
