import React, { useEffect } from 'react';
import '../styles/Modal.css';

const Modal = ({ 
    isOpen = true, 
    onClose, 
    title, 
    children, 
    size = 'medium',
    showCloseButton = true,
    closeOnOverlayClick = true,
    closeOnEsc = true,
    className = ''
}) => {
    useEffect(() => {
        if (isOpen && closeOnEsc) {
            const handleEsc = (e) => {
                if (e.keyCode === 27) {
                    onClose();
                }
            };
            document.addEventListener('keydown', handleEsc);
            return () => document.removeEventListener('keydown', handleEsc);
        }
    }, [isOpen, closeOnEsc, onClose]);

    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'auto';
        }
        
        return () => {
            document.body.style.overflow = 'auto';
        };
    }, [isOpen]);

    if (!isOpen) return null;

    const handleOverlayClick = (e) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) {
            onClose();
        }
    };

    const getSizeClass = () => {
        const sizes = {
            'small': 'modal-small',
            'medium': 'modal-medium',
            'large': 'modal-large',
            'fullscreen': 'modal-fullscreen'
        };
        return sizes[size] || 'modal-medium';
    };

    return (
        <div className="modal-overlay" onClick={handleOverlayClick}>
            <div className={`modal-container ${getSizeClass()} ${className}`}>
                {(title || showCloseButton) && (
                    <div className="modal-header">
                        {title && <h2 className="modal-title">{title}</h2>}
                        {showCloseButton && (
                            <button 
                                className="modal-close-button"
                                onClick={onClose}
                                aria-label="Close modal"
                            >
                                ✕
                            </button>
                        )}
                    </div>
                )}
                
                <div className="modal-content">
                    {children}
                </div>
            </div>
        </div>
    );
};

// Confirmation Modal Component
export const ConfirmModal = ({ 
    isOpen, 
    onClose, 
    onConfirm, 
    title = "Confirm Action",
    message = "Are you sure you want to proceed?",
    confirmText = "Confirm",
    cancelText = "Cancel",
    type = "default" // default, danger, warning, success
}) => {
    const getTypeClass = () => {
        return `confirm-modal-${type}`;
    };

    return (
        <Modal 
            isOpen={isOpen} 
            onClose={onClose} 
            title={title}
            size="small"
            className={`confirm-modal ${getTypeClass()}`}
        >
// Confirmation Modal Component
export const ConfirmModal = ({ 
    isOpen, 
    onClose, 
    onConfirm, 
    title = "Confirm Action",
    message = "Are you sure you want to proceed?",
    confirmText = "Confirm",
    cancelText = "Cancel",
    type = "default" // default, danger, warning, success
}) => {
    const getTypeClass = () => {
        return `confirm-modal-${type}`;
    };

    const getTypeIcon = () => {
        const icons = {
            'danger': '⚠️',
            'warning': '🚨',
            'success': '✅',
            'info': 'ℹ️',
            'default': '❓'
        };
        return icons[type] || icons.default;
    };

    return (
        <Modal 
            isOpen={isOpen} 
            onClose={onClose} 
            title={title}
            size="small"
            className={`confirm-modal ${getTypeClass()}`}
        >
            <div className="confirm-modal-content">
                <div className="confirm-message">
                    <span className="confirm-icon">{getTypeIcon()}</span>
                    <p>{message}</p>
                </div>
                
                <div className="confirm-actions">
                    <button 
                        className="cancel-button"
                        onClick={onClose}
                    >
                        {cancelText}
                    </button>
                    <button 
                        className={`confirm-button confirm-${type}`}
                        onClick={() => {
                            onConfirm();
                            onClose();
                        }}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </Modal>
    );
};

// Loading Modal Component
export const LoadingModal = ({ 
    isOpen, 
    title = "Loading...", 
    message = "Please wait while we process your request",
    progress = null // 0-100 for progress bar
}) => {
    return (
        <Modal 
            isOpen={isOpen} 
            title={title}
            size="small"
            className="loading-modal"
            showCloseButton={false}
            closeOnOverlayClick={false}
            closeOnEsc={false}
        >
            <div className="loading-modal-content">
                <div className="loading-spinner">
                    <div className="spinner"></div>
                </div>
                
                <p className="loading-message">{message}</p>
                
                {progress !== null && (
                    <div className="progress-container">
                        <div className="progress-bar">
                            <div 
                                className="progress-fill"
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                        <span className="progress-text">{progress}%</span>
                    </div>
                )}
            </div>
        </Modal>
    );
};

// Image Preview Modal Component
export const ImagePreviewModal = ({ 
    isOpen, 
    onClose, 
    imageUrl, 
    title = "Image Preview",
    description = ""
}) => {
    return (
        <Modal 
            isOpen={isOpen} 
            onClose={onClose} 
            title={title}
            size="large"
            className="image-preview-modal"
        >
            <div className="image-preview-content">
                <div className="image-container">
                    <img 
                        src={imageUrl} 
                        alt={title}
                        onError={(e) => {
                            e.target.src = '/images/image-error.jpg';
                        }}
                    />
                </div>
                
                {description && (
                    <div className="image-description">
                        <p>{description}</p>
                    </div>
                )}
                
                <div className="image-actions">
                    <button 
                        className="download-button"
                        onClick={() => {
                            const link = document.createElement('a');
                            link.href = imageUrl;
                            link.download = title || 'image';
                            link.click();
                        }}
                    >
                        📥 Download
                    </button>
                    
                    <button 
                        className="share-button"
                        onClick={() => {
                            if (navigator.share) {
                                navigator.share({
                                    title: title,
                                    text: description,
                                    url: imageUrl
                                });
                            } else {
                                navigator.clipboard.writeText(imageUrl);
                                alert('Image URL copied to clipboard!');
                            }
                        }}
                    >
                        📤 Share
                    </button>
                </div>
            </div>
        </Modal>
    );
};

// Form Modal Component
export const FormModal = ({ 
    isOpen, 
    onClose, 
    onSubmit, 
    title, 
    fields = [],
    submitText = "Submit",
    cancelText = "Cancel",
    initialData = {}
}) => {
    const [formData, setFormData] = React.useState(initialData);
    const [errors, setErrors] = React.useState({});

    React.useEffect(() => {
        setFormData(initialData);
        setErrors({});
    }, [isOpen, initialData]);

    const handleFieldChange = (fieldName, value) => {
        setFormData(prev => ({
            ...prev,
            [fieldName]: value
        }));
        
        // Clear error for this field
        if (errors[fieldName]) {
            setErrors(prev => ({
                ...prev,
                [fieldName]: null
            }));
        }
    };

    const validateForm = () => {
        const newErrors = {};
        
        fields.forEach(field => {
            if (field.required && !formData[field.name]) {
                newErrors[field.name] = `${field.label} is required`;
            }
            
            if (field.validation && formData[field.name]) {
                const validationResult = field.validation(formData[field.name]);
                if (validationResult !== true) {
                    newErrors[field.name] = validationResult;
                }
            }
        });
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        
        if (validateForm()) {
            onSubmit(formData);
            onClose();
        }
    };

    const renderField = (field) => {
        const { name, type = 'text', label, placeholder, options, required } = field;
        const value = formData[name] || '';
        const error = errors[name];

        switch (type) {
            case 'select':
                return (
                    <select
                        value={value}
                        onChange={(e) => handleFieldChange(name, e.target.value)}
                        required={required}
                    >
                        <option value="">{placeholder || `Select ${label}`}</option>
                        {options.map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                );
            
            case 'textarea':
                return (
                    <textarea
                        value={value}
                        placeholder={placeholder}
                        onChange={(e) => handleFieldChange(name, e.target.value)}
                        required={required}
                        rows={4}
                    />
                );
            
            case 'checkbox':
                return (
                    <label className="checkbox-field">
                        <input
                            type="checkbox"
                            checked={value}
                            onChange={(e) => handleFieldChange(name, e.target.checked)}
                        />
                        <span>{label}</span>
                    </label>
                );
            
            default:
                return (
                    <input
                        type={type}
                        value={value}
                        placeholder={placeholder}
                        onChange={(e) => handleFieldChange(name, e.target.value)}
                        required={required}
                    />
                );
        }
    };

    return (
        <Modal 
            isOpen={isOpen} 
            onClose={onClose} 
            title={title}
            size="medium"
            className="form-modal"
        >
            <form onSubmit={handleSubmit} className="modal-form">
                <div className="form-fields">
                    {fields.map(field => (
                        <div key={field.name} className="form-field">
                            {field.type !== 'checkbox' && (
                                <label className="field-label">
                                    {field.label}
                                    {field.required && <span className="required">*</span>}
                                </label>
                            )}
                            
                            <div className="field-input">
                                {renderField(field)}
                            </div>
                            
                            {errors[field.name] && (
                                <span className="field-error">{errors[field.name]}</span>
                            )}
                        </div>
                    ))}
                </div>
                
                <div className="form-actions">
                    <button 
                        type="button" 
                        className="cancel-button"
                        onClick={onClose}
                    >
                        {cancelText}
                    </button>
                    <button 
                        type="submit" 
                        className="submit-button"
                    >
                        {submitText}
                    </button>
                </div>
            </form>
        </Modal>
    );
};

export default Modal;