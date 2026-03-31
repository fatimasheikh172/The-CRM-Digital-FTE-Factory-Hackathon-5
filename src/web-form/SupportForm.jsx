/**
 * TechCorp Support Form Component
 * 
 * A complete React component for customer support form submission.
 * Uses Tailwind CSS for styling.
 * 
 * Props:
 * - apiUrl: API endpoint for form submission (default: /api/support/submit)
 * - onSuccess: Callback function when submission succeeds
 * - onError: Callback function when submission fails
 */

import React, { useState } from 'react';

// Category options
const CATEGORIES = [
  { value: 'General', label: 'General Inquiry' },
  { value: 'Technical', label: 'Technical Support' },
  { value: 'Billing', label: 'Billing & Payments' },
  { value: 'Bug Report', label: 'Bug Report' },
  { value: 'Feedback', label: 'Feedback' },
  { value: 'Account', label: 'Account Issues' },
  { value: 'API', label: 'API Support' },
];

// Priority options
const PRIORITIES = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];

// Form field validation rules
const VALIDATION_RULES = {
  name: {
    minLength: 2,
    maxLength: 100,
    required: true,
    pattern: /^[a-zA-Z\s]+$/,
    errorMessage: 'Please enter a valid name (2-100 characters, letters only)'
  },
  email: {
    required: true,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    errorMessage: 'Please enter a valid email address'
  },
  subject: {
    minLength: 5,
    maxLength: 200,
    required: true,
    errorMessage: 'Subject must be between 5 and 200 characters'
  },
  message: {
    minLength: 10,
    maxLength: 5000,
    required: true,
    errorMessage: 'Message must be at least 10 characters'
  }
};

export default function SupportForm({ 
  apiUrl = '/api/support/submit',
  onSuccess,
  onError 
}) {
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    category: 'General',
    priority: 'medium',
    message: ''
  });

  // UI state
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null); // 'success' | 'error' | null
  const [ticketId, setTicketId] = useState(null);
  const [touched, setTouched] = useState({});

  // Handle input change
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Handle field blur (mark as touched)
  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));
    
    // Validate field on blur
    validateField(name, formData[name]);
  };

  // Validate a single field
  const validateField = (name, value) => {
    const rules = VALIDATION_RULES[name];
    if (!rules) return true;

    // Check required
    if (rules.required && !value.trim()) {
      setErrors(prev => ({
        ...prev,
        [name]: `${name.charAt(0).toUpperCase() + name.slice(1)} is required`
      }));
      return false;
    }

    // Check min length
    if (rules.minLength && value.length < rules.minLength) {
      setErrors(prev => ({
        ...prev,
        [name]: rules.errorMessage
      }));
      return false;
    }

    // Check max length
    if (rules.maxLength && value.length > rules.maxLength) {
      setErrors(prev => ({
        ...prev,
        [name]: `Maximum ${rules.maxLength} characters allowed`
      }));
      return false;
    }

    // Check pattern
    if (rules.pattern && !rules.pattern.test(value)) {
      setErrors(prev => ({
        ...prev,
        [name]: rules.errorMessage
      }));
      return false;
    }

    return true;
  };

  // Validate entire form
  const validateForm = () => {
    const fields = ['name', 'email', 'subject', 'message'];
    let isValid = true;
    const newErrors = {};

    fields.forEach(field => {
      if (!validateField(field, formData[field])) {
        isValid = false;
      }
    });

    // Additional email validation
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Mark all fields as touched
    setTouched({
      name: true,
      email: true,
      subject: true,
      category: true,
      priority: true,
      message: true
    });

    // Validate form
    if (!validateForm()) {
      return;
    }

    // Submit
    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Submission failed');
      }

      const data = await response.json();
      
      setSubmitStatus('success');
      setTicketId(data.ticket_id);
      
      // Reset form
      setFormData({
        name: '',
        email: '',
        subject: '',
        category: 'General',
        priority: 'medium',
        message: ''
      });

      // Call success callback
      if (onSuccess) {
        onSuccess(data);
      }

    } catch (error) {
      setSubmitStatus('error');
      
      // Call error callback
      if (onError) {
        onError(error);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render input field with error styling
  const renderInput = (name, label, type = 'text', placeholder = '') => (
    <div className="mb-4">
      <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
        {label} <span className="text-red-500">*</span>
      </label>
      <input
        type={type}
        id={name}
        name={name}
        value={formData[name]}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder={placeholder}
        className={`w-full px-3 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors
          ${errors[name] && touched[name] 
            ? 'border-red-500 bg-red-50' 
            : 'border-gray-300 bg-white'
          }`}
        disabled={isSubmitting}
      />
      {errors[name] && touched[name] && (
        <p className="mt-1 text-sm text-red-600">{errors[name]}</p>
      )}
    </div>
  );

  // Render select field
  const renderSelect = (name, label, options) => (
    <div className="mb-4">
      <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        id={name}
        name={name}
        value={formData[name]}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white disabled:bg-gray-100 transition-colors"
        disabled={isSubmitting}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );

  // Render textarea field
  const renderTextarea = (name, label, placeholder, maxLength) => (
    <div className="mb-4">
      <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
        {label} <span className="text-red-500">*</span>
      </label>
      <textarea
        id={name}
        name={name}
        value={formData[name]}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder={placeholder}
        rows={5}
        maxLength={maxLength}
        className={`w-full px-3 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-y
          ${errors[name] && touched[name] 
            ? 'border-red-500 bg-red-50' 
            : 'border-gray-300 bg-white'
          }`}
        disabled={isSubmitting}
      />
      <div className="flex justify-between items-center mt-1">
        {errors[name] && touched[name] ? (
          <p className="text-sm text-red-600">{errors[name]}</p>
        ) : (
          <span></span>
        )}
        <span className={`text-sm ${formData[name].length > maxLength * 0.9 ? 'text-orange-500' : 'text-gray-500'}`}>
          {formData[name].length}/{maxLength} characters
        </span>
      </div>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg">
      {/* Header */}
      <div className="mb-6 pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">Contact Support</h2>
        <p className="mt-1 text-sm text-gray-600">
          Fill out the form below and we'll get back to you as soon as possible.
        </p>
      </div>

      {/* Success Message */}
      {submitStatus === 'success' && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-green-500 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="font-medium text-green-800">Submission Received!</h3>
              <p className="text-sm text-green-700 mt-1">
                Thank you for contacting us. Your ticket ID is <span className="font-mono font-bold">{ticketId}</span>.
                We'll respond within 24 hours.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setSubmitStatus(null)}
            className="mt-3 text-sm text-green-600 hover:text-green-800 font-medium"
          >
            Submit another request
          </button>
        </div>
      )}

      {/* Error Message */}
      {submitStatus === 'error' && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-500 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="font-medium text-red-800">Submission Failed</h3>
              <p className="text-sm text-red-700 mt-1">
                Sorry, there was an error submitting your request. Please try again.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} noValidate>
        {/* Name and Email Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {renderInput('name', 'Your Name', 'text', 'John Doe')}
          {renderInput('email', 'Email Address', 'email', 'john@example.com')}
        </div>

        {/* Subject */}
        {renderInput('subject', 'Subject', 'text', 'Brief description of your issue')}

        {/* Category and Priority Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {renderSelect('category', 'Category', CATEGORIES)}
          {renderSelect('priority', 'Priority', PRIORITIES)}
        </div>

        {/* Message */}
        {renderTextarea('message', 'Message', 'Please describe your issue in detail...', 5000)}

        {/* Submit Button */}
        <div className="mt-6">
          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-all duration-200
              ${isSubmitting 
                ? 'bg-blue-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 shadow-md hover:shadow-lg'
              }`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </span>
            ) : (
              'Submit Request'
            )}
          </button>
        </div>

        {/* Help Text */}
        <p className="mt-4 text-xs text-gray-500 text-center">
          Fields marked with <span className="text-red-500">*</span> are required.
          We typically respond within 24 hours.
        </p>
      </form>
    </div>
  );
}
