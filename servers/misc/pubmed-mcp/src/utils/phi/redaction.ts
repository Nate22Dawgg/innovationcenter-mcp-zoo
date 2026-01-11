/**
 * @fileoverview PHI (Protected Health Information) handling utilities for TypeScript.
 * 
 * Provides functions for redacting PHI from data structures before logging
 * and managing data persistence policies.
 * 
 * Aligned with Python common/phi.py for consistency.
 */

/**
 * Common PHI field patterns (case-insensitive)
 */
export const PHI_FIELD_PATTERNS: Record<string, string[]> = {
  // Direct field name matches
  name: ['name', 'first_name', 'last_name', 'firstname', 'lastname', 
         'patient_name', 'member_name', 'subscriber_name', 'provider_name'],
  ssn: ['ssn', 'social_security', 'social_security_number', 'tax_id', 'tax_id_number'],
  dob: ['dob', 'date_of_birth', 'birth_date', 'birthdate'],
  address: ['address', 'street', 'street_address', 'city', 'state', 'zip', 'zip_code', 
            'postal_code', 'address_line_1', 'address_line_2'],
  phone: ['phone', 'phone_number', 'telephone', 'mobile', 'cell'],
  email: ['email', 'email_address'],
  member_id: ['member_id', 'member_number', 'subscriber_id', 'patient_id', 
              'patient_number', 'account_number', 'policy_number'],
  medical_record: ['medical_record_number', 'mrn', 'record_number'],
  insurance: ['insurance_id', 'group_number', 'policy_id'],
  diagnosis: ['diagnosis', 'diagnosis_code', 'icd_code', 'icd10', 'icd9'],
  procedure: ['procedure', 'procedure_code', 'cpt_code', 'hcpcs_code'],
};

/**
 * Patterns for detecting PHI in values (not just field names)
 */
export const PHI_VALUE_PATTERNS = {
  ssn: /\b\d{3}-?\d{2}-?\d{4}\b/,  // SSN format: XXX-XX-XXXX
  phone: /\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/,  // Phone: XXX-XXX-XXXX
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,
  zip: /\b\d{5}(-\d{4})?\b/,  // ZIP code
};

/**
 * Redaction placeholder
 */
export const REDACTED_PLACEHOLDER = "[REDACTED]";

/**
 * Redact PHI (Protected Health Information) from a data structure.
 * 
 * This function recursively traverses objects, arrays, and other data structures
 * to identify and redact PHI fields before logging or storage.
 * 
 * @param payload - Data structure to redact (object, array, string, etc.)
 * @param fieldPatterns - Optional custom field patterns dict (defaults to PHI_FIELD_PATTERNS)
 * @returns Deep copy of payload with PHI fields redacted
 * 
 * @example
 * ```typescript
 * const data = { patient: { name: "John Doe", ssn: "123-45-6789" } };
 * redactPhi(data);
 * // Returns: { patient: { name: "[REDACTED]", ssn: "[REDACTED]" } }
 * ```
 */
export function redactPhi(
  payload: unknown,
  fieldPatterns?: Record<string, string[]>
): unknown {
  const patterns = fieldPatterns ?? PHI_FIELD_PATTERNS;
  
  // Create a flattened set of all PHI field names for quick lookup
  const phiFields = new Set<string>();
  for (const patternList of Object.values(patterns)) {
    for (const pattern of patternList) {
      phiFields.add(pattern);
    }
  }
  
  function isPhiField(key: string): boolean {
    const keyLower = key.toLowerCase();
    for (const pattern of phiFields) {
      if (pattern.toLowerCase().includes(keyLower) || keyLower.includes(pattern.toLowerCase())) {
        return true;
      }
    }
    return false;
  }
  
  function redactValue(value: string): string {
    let redacted = value;
    
    // Check for SSN pattern
    if (PHI_VALUE_PATTERNS.ssn.test(redacted)) {
      redacted = redacted.replace(PHI_VALUE_PATTERNS.ssn, REDACTED_PLACEHOLDER);
    }
    // Check for phone pattern
    if (PHI_VALUE_PATTERNS.phone.test(redacted)) {
      redacted = redacted.replace(PHI_VALUE_PATTERNS.phone, REDACTED_PLACEHOLDER);
    }
    // Check for email pattern
    if (PHI_VALUE_PATTERNS.email.test(redacted)) {
      redacted = redacted.replace(PHI_VALUE_PATTERNS.email, REDACTED_PLACEHOLDER);
    }
    
    return redacted;
  }
  
  function redactRecursive(obj: unknown): unknown {
    if (obj === null || obj === undefined) {
      return obj;
    }
    
    if (typeof obj === 'object') {
      if (Array.isArray(obj)) {
        return obj.map(item => redactRecursive(item));
      }
      
      // Handle plain objects
      const redacted: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(obj)) {
        if (isPhiField(key)) {
          // Redact the entire value
          redacted[key] = REDACTED_PLACEHOLDER;
        } else if (typeof value === 'object' && value !== null) {
          // Recursively process nested structures
          redacted[key] = redactRecursive(value);
        } else if (typeof value === 'string') {
          // Check for PHI patterns in string values
          redacted[key] = redactValue(value);
        } else {
          redacted[key] = value;
        }
      }
      return redacted;
    } else if (typeof obj === 'string') {
      return redactValue(obj);
    } else {
      return obj;
    }
  }
  
  // Create deep copy to avoid modifying original
  return redactRecursive(payload);
}

/**
 * Check if a field name matches PHI patterns.
 * 
 * @param fieldName - Field name to check
 * @param fieldPatterns - Optional custom field patterns dict
 * @returns True if field matches PHI patterns, False otherwise
 */
export function isPhiField(
  fieldName: string,
  fieldPatterns?: Record<string, string[]>
): boolean {
  const patterns = fieldPatterns ?? PHI_FIELD_PATTERNS;
  
  const phiFields = new Set<string>();
  for (const patternList of Object.values(patterns)) {
    for (const pattern of patternList) {
      phiFields.add(pattern);
    }
  }
  
  const fieldLower = fieldName.toLowerCase();
  for (const pattern of phiFields) {
    if (pattern.toLowerCase().includes(fieldLower) || fieldLower.includes(pattern.toLowerCase())) {
      return true;
    }
  }
  return false;
}

/**
 * Mark data as ephemeral (should not be persisted beyond request scope).
 * 
 * @param data - Data object to mark
 * @param reason - Optional reason for ephemeral marking
 * @returns Data object with ephemeral metadata
 */
export function markEphemeral<T extends Record<string, unknown>>(
  data: T,
  reason?: string
): T & { _persistence: { type: string; reason: string; should_persist: false } } {
  return {
    ...data,
    _persistence: {
      type: "ephemeral",
      reason: reason || "Contains PHI or sensitive data",
      should_persist: false,
    },
  };
}

/**
 * Mark data as stored (can be persisted).
 * 
 * @param data - Data object to mark
 * @param reason - Optional reason for stored marking
 * @returns Data object with persistence metadata
 */
export function markStored<T extends Record<string, unknown>>(
  data: T,
  reason?: string
): T & { _persistence: { type: string; reason: string; should_persist: true } } {
  return {
    ...data,
    _persistence: {
      type: "stored",
      reason: reason || "Safe to persist",
      should_persist: true,
    },
  };
}

/**
 * Check if data is marked as ephemeral.
 * 
 * @param data - Data object to check
 * @returns True if data is marked as ephemeral, False otherwise
 */
export function isEphemeral(data: unknown): boolean {
  if (typeof data !== 'object' || data === null) {
    return false;
  }
  
  const persistence = (data as { _persistence?: { type?: string; should_persist?: boolean } })._persistence;
  return persistence?.type === "ephemeral" || persistence?.should_persist === false;
}

/**
 * Check if data should be persisted.
 * 
 * @param data - Data object to check
 * @returns True if data should be persisted, False if ephemeral
 */
export function shouldPersist(data: unknown): boolean {
  return !isEphemeral(data);
}
