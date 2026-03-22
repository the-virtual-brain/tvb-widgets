"use strict";
(self["webpackChunk_anywidget_monorepo"] = self["webpackChunk_anywidget_monorepo"] || []).push([["241"], {
680: (function (__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) {
// ESM COMPAT FLAG
__webpack_require__.r(__webpack_exports__);

// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  "default": () => (/* binding */ src_plugin)
});

// EXTERNAL MODULE: consume shared module (default) @jupyter-widgets/base@^6 (strict)
var base_6_strict_ = __webpack_require__(319);
var base_6_strict_namespaceObject = /*#__PURE__*/__webpack_require__.t(base_6_strict_, 2);
// EXTERNAL MODULE: ./node_modules/.pnpm/@lukeed+uuid@2.0.1/node_modules/@lukeed/uuid/dist/index.mjs
var dist = __webpack_require__(101);
// EXTERNAL MODULE: ./node_modules/.pnpm/solid-js@1.9.10/node_modules/solid-js/dist/solid.js
var solid = __webpack_require__(427);
;// CONCATENATED MODULE: ./packages/anywidget/src/widget.js



/** @import * as base from "@jupyter-widgets/base" */
/** @import { Initialize, Render, AnyModel } from "@anywidget/types" */

/**
 * @template T
 * @typedef {T | PromiseLike<T>} Awaitable
 */

/**
 * @typedef AnyWidget
 * @prop initialize {Initialize}
 * @prop render {Render}
 */

/**
 *  @typedef AnyWidgetModule
 *  @prop render {Render=}
 *  @prop default {AnyWidget | (() => AnyWidget | Promise<AnyWidget>)=}
 */

/**
 * @param {unknown} condition
 * @param {string} message
 * @returns {asserts condition}
 */
function assert(condition, message) {
	if (!condition) throw new Error(message);
}

/**
 * @param {string} str
 * @returns {str is "https://${string}" | "http://${string}"}
 */
function is_href(str) {
	return str.startsWith("http://") || str.startsWith("https://");
}

/**
 * @param {string} href
 * @param {string} anywidget_id
 * @returns {Promise<void>}
 */
async function load_css_href(href, anywidget_id) {
	/** @type {HTMLLinkElement | null} */
	let prev = document.querySelector(`link[id='${anywidget_id}']`);

	// Adapted from https://github.com/vitejs/vite/blob/d59e1acc2efc0307488364e9f2fad528ec57f204/packages/vite/src/client/client.ts#L185-L201
	// Swaps out old styles with new, but avoids flash of unstyled content.
	// No need to await the load since we already have styles applied.
	if (prev) {
		let newLink = /** @type {HTMLLinkElement} */ (prev.cloneNode());
		newLink.href = href;
		newLink.addEventListener("load", () => prev?.remove());
		newLink.addEventListener("error", () => prev?.remove());
		prev.after(newLink);
		return;
	}

	return new Promise((resolve) => {
		let link = Object.assign(document.createElement("link"), {
			rel: "stylesheet",
			href,
			onload: resolve,
		});
		document.head.appendChild(link);
	});
}

/**
 * @param {string} css_text
 * @param {string} anywidget_id
 * @returns {void}
 */
function load_css_text(css_text, anywidget_id) {
	/** @type {HTMLStyleElement | null} */
	let prev = document.querySelector(`style[id='${anywidget_id}']`);
	if (prev) {
		// replace instead of creating a new DOM node
		prev.textContent = css_text;
		return;
	}
	let style = Object.assign(document.createElement("style"), {
		id: anywidget_id,
		type: "text/css",
	});
	style.appendChild(document.createTextNode(css_text));
	document.head.appendChild(style);
}

/**
 * @param {string | undefined} css
 * @param {string} anywidget_id
 * @returns {Promise<void>}
 */
async function load_css(css, anywidget_id) {
	if (!css || !anywidget_id) return;
	if (is_href(css)) return load_css_href(css, anywidget_id);
	return load_css_text(css, anywidget_id);
}

/**
 * @param {string} esm
 * @returns {Promise<AnyWidgetModule>}
 */
async function load_esm(esm) {
	if (is_href(esm)) {
		return await import(/* webpackIgnore: true */ /* @vite-ignore */ esm);
	}
	let url = URL.createObjectURL(new Blob([esm], { type: "text/javascript" }));
	let mod = await import(/* webpackIgnore: true */ /* @vite-ignore */ url);
	URL.revokeObjectURL(url);
	return mod;
}

/** @param {string} anywidget_id */
function warn_render_deprecation(anywidget_id) {
	console.warn(`\
[anywidget] Deprecation Warning for ${anywidget_id}: Direct export of a 'render' will likely be deprecated in the future. To migrate ...

Remove the 'export' keyword from 'render'
-----------------------------------------

export function render({ model, el }) { ... }
^^^^^^

Create a default export that returns an object with 'render'
------------------------------------------------------------

function render({ model, el }) { ... }
         ^^^^^^
export default { render }
                 ^^^^^^

Pin to anywidget>=0.9.0 in your pyproject.toml
----------------------------------------------

dependencies = ["anywidget>=0.9.0"]

To learn more, please see: https://github.com/manzt/anywidget/pull/395.
`);
}

/**
 * @param {string} esm
 * @param {string} anywidget_id
 * @returns {Promise<AnyWidget>}
 */
async function load_widget(esm, anywidget_id) {
	let mod = await load_esm(esm);
	if (mod.render) {
		warn_render_deprecation(anywidget_id);
		return {
			async initialize() {},
			render: mod.render,
		};
	}
	assert(
		mod.default,
		`[anywidget] module must export a default function or object.`,
	);
	let widget =
		typeof mod.default === "function" ? await mod.default() : mod.default;
	return widget;
}

/**
 * This is a trick so that we can cleanup event listeners added
 * by the user-defined function.
 */
let INITIALIZE_MARKER = Symbol("anywidget.initialize");

/**
 * @param {base.DOMWidgetModel} model
 * @param {unknown} context
 * @return {import("@anywidget/types").AnyModel}
 *
 * Prunes the view down to the minimum context necessary.
 *
 * Calls to `model.get` and `model.set` automatically add the
 * `context`, so we can gracefully unsubscribe from events
 * added by user-defined hooks.
 */
function model_proxy(model, context) {
	return {
		get: model.get.bind(model),
		set: model.set.bind(model),
		save_changes: model.save_changes.bind(model),
		send: model.send.bind(model),
		// @ts-expect-error
		on(name, callback) {
			model.on(name, callback, context);
		},
		off(name, callback) {
			model.off(name, callback, context);
		},
		// @ts-expect-error - the widget_manager type is wider than what
		// we want to expose to developers.
		// In a future version, we will expose a more limited API but
		// that can wait for a minor version bump.
		widget_manager: model.widget_manager,
	};
}

/**
 * @param {void | (() => Awaitable<void>)} fn
 * @param {string} kind
 */
async function safe_cleanup(fn, kind) {
	return Promise.resolve()
		.then(() => fn?.())
		.catch((e) => console.warn(`[anywidget] error cleaning up ${kind}.`, e));
}

/**
 * @template T
 * @typedef Ready
 * @property {"ready"} status
 * @property {T} data
 */

/**
 * @typedef Pending
 * @property {"pending"} status
 */

/**
 * @typedef Errored
 * @property {"error"} status
 * @property {unknown} error
 */

/**
 * @template T
 * @typedef {Pending | Ready<T> | Errored} Result
 */

/**
 * Cleans up the stack trace at anywidget boundary.
 * You can fully inspect the entire stack trace in the console interactively,
 * but the initial error message is cleaned up to be more user-friendly.
 *
 * @param {unknown} source
 */
function throw_anywidget_error(source) {
	if (!(source instanceof Error)) {
		// Don't know what to do with this.
		throw source;
	}
	let lines = source.stack?.split("\n") ?? [];
	let anywidget_index = lines.findIndex((line) => line.includes("anywidget"));
	let clean_stack =
		anywidget_index === -1 ? lines : lines.slice(0, anywidget_index + 1);
	source.stack = clean_stack.join("\n");
	console.error(source);
	throw source;
}

/**
 * @typedef InvokeOptions
 * @prop {DataView[]} [buffers]
 * @prop {AbortSignal} [signal]
 */

/**
 * @template T
 * @param {import("@anywidget/types").AnyModel} model
 * @param {string} name
 * @param {any} [msg]
 * @param {InvokeOptions} [options]
 * @return {Promise<[T, DataView[]]>}
 */
function invoke(model, name, msg, options = {}) {
	// crypto.randomUUID() is not available in non-secure contexts (i.e., http://)
	// so we use simple (non-secure) polyfill.
	let id = dist.v4();
	let signal = options.signal ?? AbortSignal.timeout(3000);

	return new Promise((resolve, reject) => {
		if (signal.aborted) {
			reject(signal.reason);
		}
		signal.addEventListener("abort", () => {
			model.off("msg:custom", handler);
			reject(signal.reason);
		});

		/**
		 * @param {{ id: string, kind: "anywidget-command-response", response: T }} msg
		 * @param {DataView[]} buffers
		 */
		function handler(msg, buffers) {
			if (!(msg.id === id)) return;
			resolve([msg.response, buffers]);
			model.off("msg:custom", handler);
		}
		model.on("msg:custom", handler);
		model.send(
			{ id, kind: "anywidget-command", name, msg },
			undefined,
			options.buffers ?? [],
		);
	});
}

/**
 * Polyfill for {@link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/withResolvers Promise.withResolvers}
 *
 * Trevor(2025-03-14): Should be able to remove once more stable across browsers.
 *
 * @template T
 * @returns {PromiseWithResolvers<T>}
 */
function promise_with_resolvers() {
	let resolve;
	let reject;
	let promise = new Promise((res, rej) => {
		resolve = res;
		reject = rej;
	});
	// @ts-expect-error - We know these types are ok
	return { promise, resolve, reject };
}

/**
 * @template {Record<string, unknown>} T
 * @template {keyof T & string} K
 * @param {AnyModel<T>} model
 * @param {K} name
 * @param {{ signal?: AbortSignal}} options
 * @returns {solid.Accessor<T[K]>}
 */
function observe(model, name, { signal }) {
	let [get, set] = solid/* .createSignal */.n5(model.get(name));
	let update = () => set(() => model.get(name));
	model.on(`change:${name}`, update);
	signal?.addEventListener("abort", () => {
		model.off(`change:${name}`, update);
	});
	return get;
}

/**
 * @typedef State
 * @property {string} _esm
 * @property {string} _anywidget_id
 * @property {string | undefined} _css
 */

class Runtime {
	/** @type {solid.Accessor<Result<AnyWidget>>} */
	// @ts-expect-error - Set synchronously in constructor.
	#widget_result;
	/** @type {AbortSignal} */
	#signal;
	/** @type {Promise<void>} */
	ready;

	/**
	 * @param {base.DOMWidgetModel} model
	 * @param {{ signal: AbortSignal }} options
	 */
	constructor(model, options) {
		/** @type {PromiseWithResolvers<void>} */
		let resolvers = promise_with_resolvers();
		this.ready = resolvers.promise;
		this.#signal = options.signal;
		this.#signal.throwIfAborted();
		this.#signal.addEventListener("abort", () => dispose());
		AbortSignal.timeout(2000).addEventListener("abort", () => {
			resolvers.reject(new Error("[anywidget] Failed to initialize model."));
		});
		let dispose = solid/* .createRoot */.Hr((dispose) => {
			/** @type {AnyModel<State>} */
			// @ts-expect-error - Types don't sufficiently overlap, so we cast here for type-safe access
			let typed_model = model;
			let id = typed_model.get("_anywidget_id");
			let css = observe(typed_model, "_css", { signal: this.#signal });
			let esm = observe(typed_model, "_esm", { signal: this.#signal });
			let [widget_result, set_widget_result] = solid/* .createSignal */.n5(
				/** @type {Result<AnyWidget>} */ ({ status: "pending" }),
			);
			this.#widget_result = widget_result;

			solid/* .createEffect */.EH(
				solid.on(
					css,
					() => console.debug(`[anywidget] css hot updated: ${id}`),
					{ defer: true },
				),
			);
			solid/* .createEffect */.EH(
				solid.on(
					esm,
					() => console.debug(`[anywidget] esm hot updated: ${id}`),
					{ defer: true },
				),
			);
			solid/* .createEffect */.EH(() => {
				load_css(css(), id);
			});
			solid/* .createEffect */.EH(() => {
				let controller = new AbortController();
				solid/* .onCleanup */.Ki(() => controller.abort());
				model.off(null, null, INITIALIZE_MARKER);
				load_widget(esm(), id)
					.then(async (widget) => {
						if (controller.signal.aborted) {
							return;
						}
						let cleanup = await widget.initialize?.({
							model: model_proxy(model, INITIALIZE_MARKER),
							experimental: {
								// @ts-expect-error - bind isn't working
								invoke: invoke.bind(null, model),
							},
						});
						if (controller.signal.aborted) {
							safe_cleanup(cleanup, "esm update");
							return;
						}
						controller.signal.addEventListener("abort", () =>
							safe_cleanup(cleanup, "esm update"),
						);
						set_widget_result({ status: "ready", data: widget });
						resolvers.resolve();
					})
					.catch((error) => set_widget_result({ status: "error", error }));
			});

			return dispose;
		});
	}

	/**
	 * @param {base.DOMWidgetView} view
	 * @param {{ signal: AbortSignal }} options
	 * @returns {Promise<void>}
	 */
	async create_view(view, options) {
		let model = view.model;
		let signal = AbortSignal.any([this.#signal, options.signal]); // either model or view destroyed
		signal.throwIfAborted();
		signal.addEventListener("abort", () => dispose());
		let dispose = solid/* .createRoot */.Hr((dispose) => {
			solid/* .createEffect */.EH(() => {
				// Clear all previous event listeners from this hook.
				model.off(null, null, view);
				view.$el.empty();
				let result = this.#widget_result();
				if (result.status === "pending") {
					return;
				}
				if (result.status === "error") {
					throw_anywidget_error(result.error);
					return;
				}
				let controller = new AbortController();
				solid/* .onCleanup */.Ki(() => controller.abort());
				Promise.resolve()
					.then(async () => {
						let cleanup = await result.data.render?.({
							model: model_proxy(model, view),
							el: view.el,
							experimental: {
								// @ts-expect-error - bind isn't working
								invoke: invoke.bind(null, model),
							},
						});
						if (controller.signal.aborted) {
							safe_cleanup(cleanup, "dispose view - already aborted");
							return;
						}
						controller.signal.addEventListener("abort", () =>
							safe_cleanup(cleanup, "dispose view - aborted"),
						);
					})
					.catch((error) => throw_anywidget_error(error));
			});
			return () => dispose();
		});
	}
}

// @ts-expect-error - injected by bundler
let version = "0.9.21";

/**
 * @param {base} options
 * @returns {{ AnyModel: typeof base.DOMWidgetModel, AnyView: typeof base.DOMWidgetView }}
 */
/* ESM default export */ function src_widget({ DOMWidgetModel, DOMWidgetView }) {
	/** @type {WeakMap<AnyModel, Runtime>} */
	let RUNTIMES = new WeakMap();

	class AnyModel extends DOMWidgetModel {
		static model_name = "AnyModel";
		static model_module = "anywidget";
		static model_module_version = version;

		static view_name = "AnyView";
		static view_module = "anywidget";
		static view_module_version = version;

		/** @param {Parameters<InstanceType<DOMWidgetModel>["initialize"]>} args */
		initialize(...args) {
			super.initialize(...args);
			let controller = new AbortController();
			this.once("destroy", () => {
				controller.abort("[anywidget] Runtime destroyed.");
				RUNTIMES.delete(this);
			});
			RUNTIMES.set(this, new Runtime(this, { signal: controller.signal }));
		}

		/** @param {Parameters<InstanceType<DOMWidgetModel>["_handle_comm_msg"]>} msg */
		async _handle_comm_msg(...msg) {
			let runtime = RUNTIMES.get(this);
			await runtime?.ready;
			return super._handle_comm_msg(...msg);
		}

		/**
		 * @param {Record<string, any>} state
		 *
		 * We override to support binary trailets because JSON.parse(JSON.stringify())
		 * does not properly clone binary data (it just returns an empty object).
		 *
		 * https://github.com/jupyter-widgets/ipywidgets/blob/47058a373d2c2b3acf101677b2745e14b76dd74b/packages/base/src/widget.ts#L562-L583
		 */
		serialize(state) {
			let serializers =
				/** @type {DOMWidgetModel} */ (this.constructor).serializers || {};
			for (let k of Object.keys(state)) {
				try {
					let serialize = serializers[k]?.serialize;
					if (serialize) {
						state[k] = serialize(state[k], this);
					} else if (k === "layout" || k === "style") {
						// These keys come from ipywidgets, rely on JSON.stringify trick.
						state[k] = JSON.parse(JSON.stringify(state[k]));
					} else {
						state[k] = structuredClone(state[k]);
					}
					if (typeof state[k]?.toJSON === "function") {
						state[k] = state[k].toJSON();
					}
				} catch (e) {
					console.error("Error serializing widget state attribute: ", k);
					throw e;
				}
			}
			return state;
		}
	}

	class AnyView extends DOMWidgetView {
		#controller = new AbortController();
		async render() {
			let runtime = RUNTIMES.get(this.model);
			assert(runtime, "[anywidget] Runtime not found.");
			await runtime.create_view(this, { signal: this.#controller.signal });
		}
		remove() {
			this.#controller.abort("[anywidget] View destroyed.");
			super.remove();
		}
	}

	return { AnyModel, AnyView };
}

;// CONCATENATED MODULE: ./packages/anywidget/src/plugin.js



/**
 * @typedef JupyterLabRegistry
 * @property {(widget: { name: string, version: string, exports: any }) => void} registerWidget
 */

/* ESM default export */ const src_plugin = ({
	id: "anywidget:plugin",
	requires: [/** @type{unknown} */ (base_6_strict_.IJupyterWidgetRegistry)],
	activate: (
		/** @type {unknown} */ _app,
		/** @type {JupyterLabRegistry} */ registry,
	) => {
		let exports = src_widget(base_6_strict_namespaceObject);
		registry.registerWidget({
			name: "anywidget",
			// @ts-expect-error Added by bundler
			version: "0.9.21",
			exports,
		});
	},
	autoStart: true,
});


}),

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiMjQxLjU4YWI3OGEwLmpzIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vQGFueXdpZGdldC9tb25vcmVwby8uL3BhY2thZ2VzL2FueXdpZGdldC9zcmMvd2lkZ2V0LmpzIiwid2VicGFjazovL0Bhbnl3aWRnZXQvbW9ub3JlcG8vLi9wYWNrYWdlcy9hbnl3aWRnZXQvc3JjL3BsdWdpbi5qcyJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgKiBhcyB1dWlkIGZyb20gXCJAbHVrZWVkL3V1aWRcIjtcbmltcG9ydCAqIGFzIHNvbGlkIGZyb20gXCJzb2xpZC1qc1wiO1xuXG4vKiogQGltcG9ydCAqIGFzIGJhc2UgZnJvbSBcIkBqdXB5dGVyLXdpZGdldHMvYmFzZVwiICovXG4vKiogQGltcG9ydCB7IEluaXRpYWxpemUsIFJlbmRlciwgQW55TW9kZWwgfSBmcm9tIFwiQGFueXdpZGdldC90eXBlc1wiICovXG5cbi8qKlxuICogQHRlbXBsYXRlIFRcbiAqIEB0eXBlZGVmIHtUIHwgUHJvbWlzZUxpa2U8VD59IEF3YWl0YWJsZVxuICovXG5cbi8qKlxuICogQHR5cGVkZWYgQW55V2lkZ2V0XG4gKiBAcHJvcCBpbml0aWFsaXplIHtJbml0aWFsaXplfVxuICogQHByb3AgcmVuZGVyIHtSZW5kZXJ9XG4gKi9cblxuLyoqXG4gKiAgQHR5cGVkZWYgQW55V2lkZ2V0TW9kdWxlXG4gKiAgQHByb3AgcmVuZGVyIHtSZW5kZXI9fVxuICogIEBwcm9wIGRlZmF1bHQge0FueVdpZGdldCB8ICgoKSA9PiBBbnlXaWRnZXQgfCBQcm9taXNlPEFueVdpZGdldD4pPX1cbiAqL1xuXG4vKipcbiAqIEBwYXJhbSB7dW5rbm93bn0gY29uZGl0aW9uXG4gKiBAcGFyYW0ge3N0cmluZ30gbWVzc2FnZVxuICogQHJldHVybnMge2Fzc2VydHMgY29uZGl0aW9ufVxuICovXG5mdW5jdGlvbiBhc3NlcnQoY29uZGl0aW9uLCBtZXNzYWdlKSB7XG5cdGlmICghY29uZGl0aW9uKSB0aHJvdyBuZXcgRXJyb3IobWVzc2FnZSk7XG59XG5cbi8qKlxuICogQHBhcmFtIHtzdHJpbmd9IHN0clxuICogQHJldHVybnMge3N0ciBpcyBcImh0dHBzOi8vJHtzdHJpbmd9XCIgfCBcImh0dHA6Ly8ke3N0cmluZ31cIn1cbiAqL1xuZnVuY3Rpb24gaXNfaHJlZihzdHIpIHtcblx0cmV0dXJuIHN0ci5zdGFydHNXaXRoKFwiaHR0cDovL1wiKSB8fCBzdHIuc3RhcnRzV2l0aChcImh0dHBzOi8vXCIpO1xufVxuXG4vKipcbiAqIEBwYXJhbSB7c3RyaW5nfSBocmVmXG4gKiBAcGFyYW0ge3N0cmluZ30gYW55d2lkZ2V0X2lkXG4gKiBAcmV0dXJucyB7UHJvbWlzZTx2b2lkPn1cbiAqL1xuYXN5bmMgZnVuY3Rpb24gbG9hZF9jc3NfaHJlZihocmVmLCBhbnl3aWRnZXRfaWQpIHtcblx0LyoqIEB0eXBlIHtIVE1MTGlua0VsZW1lbnQgfCBudWxsfSAqL1xuXHRsZXQgcHJldiA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoYGxpbmtbaWQ9JyR7YW55d2lkZ2V0X2lkfSddYCk7XG5cblx0Ly8gQWRhcHRlZCBmcm9tIGh0dHBzOi8vZ2l0aHViLmNvbS92aXRlanMvdml0ZS9ibG9iL2Q1OWUxYWNjMmVmYzAzMDc0ODgzNjRlOWYyZmFkNTI4ZWM1N2YyMDQvcGFja2FnZXMvdml0ZS9zcmMvY2xpZW50L2NsaWVudC50cyNMMTg1LUwyMDFcblx0Ly8gU3dhcHMgb3V0IG9sZCBzdHlsZXMgd2l0aCBuZXcsIGJ1dCBhdm9pZHMgZmxhc2ggb2YgdW5zdHlsZWQgY29udGVudC5cblx0Ly8gTm8gbmVlZCB0byBhd2FpdCB0aGUgbG9hZCBzaW5jZSB3ZSBhbHJlYWR5IGhhdmUgc3R5bGVzIGFwcGxpZWQuXG5cdGlmIChwcmV2KSB7XG5cdFx0bGV0IG5ld0xpbmsgPSAvKiogQHR5cGUge0hUTUxMaW5rRWxlbWVudH0gKi8gKHByZXYuY2xvbmVOb2RlKCkpO1xuXHRcdG5ld0xpbmsuaHJlZiA9IGhyZWY7XG5cdFx0bmV3TGluay5hZGRFdmVudExpc3RlbmVyKFwibG9hZFwiLCAoKSA9PiBwcmV2Py5yZW1vdmUoKSk7XG5cdFx0bmV3TGluay5hZGRFdmVudExpc3RlbmVyKFwiZXJyb3JcIiwgKCkgPT4gcHJldj8ucmVtb3ZlKCkpO1xuXHRcdHByZXYuYWZ0ZXIobmV3TGluayk7XG5cdFx0cmV0dXJuO1xuXHR9XG5cblx0cmV0dXJuIG5ldyBQcm9taXNlKChyZXNvbHZlKSA9PiB7XG5cdFx0bGV0IGxpbmsgPSBPYmplY3QuYXNzaWduKGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoXCJsaW5rXCIpLCB7XG5cdFx0XHRyZWw6IFwic3R5bGVzaGVldFwiLFxuXHRcdFx0aHJlZixcblx0XHRcdG9ubG9hZDogcmVzb2x2ZSxcblx0XHR9KTtcblx0XHRkb2N1bWVudC5oZWFkLmFwcGVuZENoaWxkKGxpbmspO1xuXHR9KTtcbn1cblxuLyoqXG4gKiBAcGFyYW0ge3N0cmluZ30gY3NzX3RleHRcbiAqIEBwYXJhbSB7c3RyaW5nfSBhbnl3aWRnZXRfaWRcbiAqIEByZXR1cm5zIHt2b2lkfVxuICovXG5mdW5jdGlvbiBsb2FkX2Nzc190ZXh0KGNzc190ZXh0LCBhbnl3aWRnZXRfaWQpIHtcblx0LyoqIEB0eXBlIHtIVE1MU3R5bGVFbGVtZW50IHwgbnVsbH0gKi9cblx0bGV0IHByZXYgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKGBzdHlsZVtpZD0nJHthbnl3aWRnZXRfaWR9J11gKTtcblx0aWYgKHByZXYpIHtcblx0XHQvLyByZXBsYWNlIGluc3RlYWQgb2YgY3JlYXRpbmcgYSBuZXcgRE9NIG5vZGVcblx0XHRwcmV2LnRleHRDb250ZW50ID0gY3NzX3RleHQ7XG5cdFx0cmV0dXJuO1xuXHR9XG5cdGxldCBzdHlsZSA9IE9iamVjdC5hc3NpZ24oZG9jdW1lbnQuY3JlYXRlRWxlbWVudChcInN0eWxlXCIpLCB7XG5cdFx0aWQ6IGFueXdpZGdldF9pZCxcblx0XHR0eXBlOiBcInRleHQvY3NzXCIsXG5cdH0pO1xuXHRzdHlsZS5hcHBlbmRDaGlsZChkb2N1bWVudC5jcmVhdGVUZXh0Tm9kZShjc3NfdGV4dCkpO1xuXHRkb2N1bWVudC5oZWFkLmFwcGVuZENoaWxkKHN0eWxlKTtcbn1cblxuLyoqXG4gKiBAcGFyYW0ge3N0cmluZyB8IHVuZGVmaW5lZH0gY3NzXG4gKiBAcGFyYW0ge3N0cmluZ30gYW55d2lkZ2V0X2lkXG4gKiBAcmV0dXJucyB7UHJvbWlzZTx2b2lkPn1cbiAqL1xuYXN5bmMgZnVuY3Rpb24gbG9hZF9jc3MoY3NzLCBhbnl3aWRnZXRfaWQpIHtcblx0aWYgKCFjc3MgfHwgIWFueXdpZGdldF9pZCkgcmV0dXJuO1xuXHRpZiAoaXNfaHJlZihjc3MpKSByZXR1cm4gbG9hZF9jc3NfaHJlZihjc3MsIGFueXdpZGdldF9pZCk7XG5cdHJldHVybiBsb2FkX2Nzc190ZXh0KGNzcywgYW55d2lkZ2V0X2lkKTtcbn1cblxuLyoqXG4gKiBAcGFyYW0ge3N0cmluZ30gZXNtXG4gKiBAcmV0dXJucyB7UHJvbWlzZTxBbnlXaWRnZXRNb2R1bGU+fVxuICovXG5hc3luYyBmdW5jdGlvbiBsb2FkX2VzbShlc20pIHtcblx0aWYgKGlzX2hyZWYoZXNtKSkge1xuXHRcdHJldHVybiBhd2FpdCBpbXBvcnQoLyogd2VicGFja0lnbm9yZTogdHJ1ZSAqLyAvKiBAdml0ZS1pZ25vcmUgKi8gZXNtKTtcblx0fVxuXHRsZXQgdXJsID0gVVJMLmNyZWF0ZU9iamVjdFVSTChuZXcgQmxvYihbZXNtXSwgeyB0eXBlOiBcInRleHQvamF2YXNjcmlwdFwiIH0pKTtcblx0bGV0IG1vZCA9IGF3YWl0IGltcG9ydCgvKiB3ZWJwYWNrSWdub3JlOiB0cnVlICovIC8qIEB2aXRlLWlnbm9yZSAqLyB1cmwpO1xuXHRVUkwucmV2b2tlT2JqZWN0VVJMKHVybCk7XG5cdHJldHVybiBtb2Q7XG59XG5cbi8qKiBAcGFyYW0ge3N0cmluZ30gYW55d2lkZ2V0X2lkICovXG5mdW5jdGlvbiB3YXJuX3JlbmRlcl9kZXByZWNhdGlvbihhbnl3aWRnZXRfaWQpIHtcblx0Y29uc29sZS53YXJuKGBcXFxuW2FueXdpZGdldF0gRGVwcmVjYXRpb24gV2FybmluZyBmb3IgJHthbnl3aWRnZXRfaWR9OiBEaXJlY3QgZXhwb3J0IG9mIGEgJ3JlbmRlcicgd2lsbCBsaWtlbHkgYmUgZGVwcmVjYXRlZCBpbiB0aGUgZnV0dXJlLiBUbyBtaWdyYXRlIC4uLlxuXG5SZW1vdmUgdGhlICdleHBvcnQnIGtleXdvcmQgZnJvbSAncmVuZGVyJ1xuLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cblxuZXhwb3J0IGZ1bmN0aW9uIHJlbmRlcih7IG1vZGVsLCBlbCB9KSB7IC4uLiB9XG5eXl5eXl5cblxuQ3JlYXRlIGEgZGVmYXVsdCBleHBvcnQgdGhhdCByZXR1cm5zIGFuIG9iamVjdCB3aXRoICdyZW5kZXInXG4tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cblxuZnVuY3Rpb24gcmVuZGVyKHsgbW9kZWwsIGVsIH0pIHsgLi4uIH1cbiAgICAgICAgIF5eXl5eXlxuZXhwb3J0IGRlZmF1bHQgeyByZW5kZXIgfVxuICAgICAgICAgICAgICAgICBeXl5eXl5cblxuUGluIHRvIGFueXdpZGdldD49MC45LjAgaW4geW91ciBweXByb2plY3QudG9tbFxuLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuXG5kZXBlbmRlbmNpZXMgPSBbXCJhbnl3aWRnZXQ+PTAuOS4wXCJdXG5cblRvIGxlYXJuIG1vcmUsIHBsZWFzZSBzZWU6IGh0dHBzOi8vZ2l0aHViLmNvbS9tYW56dC9hbnl3aWRnZXQvcHVsbC8zOTUuXG5gKTtcbn1cblxuLyoqXG4gKiBAcGFyYW0ge3N0cmluZ30gZXNtXG4gKiBAcGFyYW0ge3N0cmluZ30gYW55d2lkZ2V0X2lkXG4gKiBAcmV0dXJucyB7UHJvbWlzZTxBbnlXaWRnZXQ+fVxuICovXG5hc3luYyBmdW5jdGlvbiBsb2FkX3dpZGdldChlc20sIGFueXdpZGdldF9pZCkge1xuXHRsZXQgbW9kID0gYXdhaXQgbG9hZF9lc20oZXNtKTtcblx0aWYgKG1vZC5yZW5kZXIpIHtcblx0XHR3YXJuX3JlbmRlcl9kZXByZWNhdGlvbihhbnl3aWRnZXRfaWQpO1xuXHRcdHJldHVybiB7XG5cdFx0XHRhc3luYyBpbml0aWFsaXplKCkge30sXG5cdFx0XHRyZW5kZXI6IG1vZC5yZW5kZXIsXG5cdFx0fTtcblx0fVxuXHRhc3NlcnQoXG5cdFx0bW9kLmRlZmF1bHQsXG5cdFx0YFthbnl3aWRnZXRdIG1vZHVsZSBtdXN0IGV4cG9ydCBhIGRlZmF1bHQgZnVuY3Rpb24gb3Igb2JqZWN0LmAsXG5cdCk7XG5cdGxldCB3aWRnZXQgPVxuXHRcdHR5cGVvZiBtb2QuZGVmYXVsdCA9PT0gXCJmdW5jdGlvblwiID8gYXdhaXQgbW9kLmRlZmF1bHQoKSA6IG1vZC5kZWZhdWx0O1xuXHRyZXR1cm4gd2lkZ2V0O1xufVxuXG4vKipcbiAqIFRoaXMgaXMgYSB0cmljayBzbyB0aGF0IHdlIGNhbiBjbGVhbnVwIGV2ZW50IGxpc3RlbmVycyBhZGRlZFxuICogYnkgdGhlIHVzZXItZGVmaW5lZCBmdW5jdGlvbi5cbiAqL1xubGV0IElOSVRJQUxJWkVfTUFSS0VSID0gU3ltYm9sKFwiYW55d2lkZ2V0LmluaXRpYWxpemVcIik7XG5cbi8qKlxuICogQHBhcmFtIHtiYXNlLkRPTVdpZGdldE1vZGVsfSBtb2RlbFxuICogQHBhcmFtIHt1bmtub3dufSBjb250ZXh0XG4gKiBAcmV0dXJuIHtpbXBvcnQoXCJAYW55d2lkZ2V0L3R5cGVzXCIpLkFueU1vZGVsfVxuICpcbiAqIFBydW5lcyB0aGUgdmlldyBkb3duIHRvIHRoZSBtaW5pbXVtIGNvbnRleHQgbmVjZXNzYXJ5LlxuICpcbiAqIENhbGxzIHRvIGBtb2RlbC5nZXRgIGFuZCBgbW9kZWwuc2V0YCBhdXRvbWF0aWNhbGx5IGFkZCB0aGVcbiAqIGBjb250ZXh0YCwgc28gd2UgY2FuIGdyYWNlZnVsbHkgdW5zdWJzY3JpYmUgZnJvbSBldmVudHNcbiAqIGFkZGVkIGJ5IHVzZXItZGVmaW5lZCBob29rcy5cbiAqL1xuZnVuY3Rpb24gbW9kZWxfcHJveHkobW9kZWwsIGNvbnRleHQpIHtcblx0cmV0dXJuIHtcblx0XHRnZXQ6IG1vZGVsLmdldC5iaW5kKG1vZGVsKSxcblx0XHRzZXQ6IG1vZGVsLnNldC5iaW5kKG1vZGVsKSxcblx0XHRzYXZlX2NoYW5nZXM6IG1vZGVsLnNhdmVfY2hhbmdlcy5iaW5kKG1vZGVsKSxcblx0XHRzZW5kOiBtb2RlbC5zZW5kLmJpbmQobW9kZWwpLFxuXHRcdC8vIEB0cy1leHBlY3QtZXJyb3Jcblx0XHRvbihuYW1lLCBjYWxsYmFjaykge1xuXHRcdFx0bW9kZWwub24obmFtZSwgY2FsbGJhY2ssIGNvbnRleHQpO1xuXHRcdH0sXG5cdFx0b2ZmKG5hbWUsIGNhbGxiYWNrKSB7XG5cdFx0XHRtb2RlbC5vZmYobmFtZSwgY2FsbGJhY2ssIGNvbnRleHQpO1xuXHRcdH0sXG5cdFx0Ly8gQHRzLWV4cGVjdC1lcnJvciAtIHRoZSB3aWRnZXRfbWFuYWdlciB0eXBlIGlzIHdpZGVyIHRoYW4gd2hhdFxuXHRcdC8vIHdlIHdhbnQgdG8gZXhwb3NlIHRvIGRldmVsb3BlcnMuXG5cdFx0Ly8gSW4gYSBmdXR1cmUgdmVyc2lvbiwgd2Ugd2lsbCBleHBvc2UgYSBtb3JlIGxpbWl0ZWQgQVBJIGJ1dFxuXHRcdC8vIHRoYXQgY2FuIHdhaXQgZm9yIGEgbWlub3IgdmVyc2lvbiBidW1wLlxuXHRcdHdpZGdldF9tYW5hZ2VyOiBtb2RlbC53aWRnZXRfbWFuYWdlcixcblx0fTtcbn1cblxuLyoqXG4gKiBAcGFyYW0ge3ZvaWQgfCAoKCkgPT4gQXdhaXRhYmxlPHZvaWQ+KX0gZm5cbiAqIEBwYXJhbSB7c3RyaW5nfSBraW5kXG4gKi9cbmFzeW5jIGZ1bmN0aW9uIHNhZmVfY2xlYW51cChmbiwga2luZCkge1xuXHRyZXR1cm4gUHJvbWlzZS5yZXNvbHZlKClcblx0XHQudGhlbigoKSA9PiBmbj8uKCkpXG5cdFx0LmNhdGNoKChlKSA9PiBjb25zb2xlLndhcm4oYFthbnl3aWRnZXRdIGVycm9yIGNsZWFuaW5nIHVwICR7a2luZH0uYCwgZSkpO1xufVxuXG4vKipcbiAqIEB0ZW1wbGF0ZSBUXG4gKiBAdHlwZWRlZiBSZWFkeVxuICogQHByb3BlcnR5IHtcInJlYWR5XCJ9IHN0YXR1c1xuICogQHByb3BlcnR5IHtUfSBkYXRhXG4gKi9cblxuLyoqXG4gKiBAdHlwZWRlZiBQZW5kaW5nXG4gKiBAcHJvcGVydHkge1wicGVuZGluZ1wifSBzdGF0dXNcbiAqL1xuXG4vKipcbiAqIEB0eXBlZGVmIEVycm9yZWRcbiAqIEBwcm9wZXJ0eSB7XCJlcnJvclwifSBzdGF0dXNcbiAqIEBwcm9wZXJ0eSB7dW5rbm93bn0gZXJyb3JcbiAqL1xuXG4vKipcbiAqIEB0ZW1wbGF0ZSBUXG4gKiBAdHlwZWRlZiB7UGVuZGluZyB8IFJlYWR5PFQ+IHwgRXJyb3JlZH0gUmVzdWx0XG4gKi9cblxuLyoqXG4gKiBDbGVhbnMgdXAgdGhlIHN0YWNrIHRyYWNlIGF0IGFueXdpZGdldCBib3VuZGFyeS5cbiAqIFlvdSBjYW4gZnVsbHkgaW5zcGVjdCB0aGUgZW50aXJlIHN0YWNrIHRyYWNlIGluIHRoZSBjb25zb2xlIGludGVyYWN0aXZlbHksXG4gKiBidXQgdGhlIGluaXRpYWwgZXJyb3IgbWVzc2FnZSBpcyBjbGVhbmVkIHVwIHRvIGJlIG1vcmUgdXNlci1mcmllbmRseS5cbiAqXG4gKiBAcGFyYW0ge3Vua25vd259IHNvdXJjZVxuICovXG5mdW5jdGlvbiB0aHJvd19hbnl3aWRnZXRfZXJyb3Ioc291cmNlKSB7XG5cdGlmICghKHNvdXJjZSBpbnN0YW5jZW9mIEVycm9yKSkge1xuXHRcdC8vIERvbid0IGtub3cgd2hhdCB0byBkbyB3aXRoIHRoaXMuXG5cdFx0dGhyb3cgc291cmNlO1xuXHR9XG5cdGxldCBsaW5lcyA9IHNvdXJjZS5zdGFjaz8uc3BsaXQoXCJcXG5cIikgPz8gW107XG5cdGxldCBhbnl3aWRnZXRfaW5kZXggPSBsaW5lcy5maW5kSW5kZXgoKGxpbmUpID0+IGxpbmUuaW5jbHVkZXMoXCJhbnl3aWRnZXRcIikpO1xuXHRsZXQgY2xlYW5fc3RhY2sgPVxuXHRcdGFueXdpZGdldF9pbmRleCA9PT0gLTEgPyBsaW5lcyA6IGxpbmVzLnNsaWNlKDAsIGFueXdpZGdldF9pbmRleCArIDEpO1xuXHRzb3VyY2Uuc3RhY2sgPSBjbGVhbl9zdGFjay5qb2luKFwiXFxuXCIpO1xuXHRjb25zb2xlLmVycm9yKHNvdXJjZSk7XG5cdHRocm93IHNvdXJjZTtcbn1cblxuLyoqXG4gKiBAdHlwZWRlZiBJbnZva2VPcHRpb25zXG4gKiBAcHJvcCB7RGF0YVZpZXdbXX0gW2J1ZmZlcnNdXG4gKiBAcHJvcCB7QWJvcnRTaWduYWx9IFtzaWduYWxdXG4gKi9cblxuLyoqXG4gKiBAdGVtcGxhdGUgVFxuICogQHBhcmFtIHtpbXBvcnQoXCJAYW55d2lkZ2V0L3R5cGVzXCIpLkFueU1vZGVsfSBtb2RlbFxuICogQHBhcmFtIHtzdHJpbmd9IG5hbWVcbiAqIEBwYXJhbSB7YW55fSBbbXNnXVxuICogQHBhcmFtIHtJbnZva2VPcHRpb25zfSBbb3B0aW9uc11cbiAqIEByZXR1cm4ge1Byb21pc2U8W1QsIERhdGFWaWV3W11dPn1cbiAqL1xuZXhwb3J0IGZ1bmN0aW9uIGludm9rZShtb2RlbCwgbmFtZSwgbXNnLCBvcHRpb25zID0ge30pIHtcblx0Ly8gY3J5cHRvLnJhbmRvbVVVSUQoKSBpcyBub3QgYXZhaWxhYmxlIGluIG5vbi1zZWN1cmUgY29udGV4dHMgKGkuZS4sIGh0dHA6Ly8pXG5cdC8vIHNvIHdlIHVzZSBzaW1wbGUgKG5vbi1zZWN1cmUpIHBvbHlmaWxsLlxuXHRsZXQgaWQgPSB1dWlkLnY0KCk7XG5cdGxldCBzaWduYWwgPSBvcHRpb25zLnNpZ25hbCA/PyBBYm9ydFNpZ25hbC50aW1lb3V0KDMwMDApO1xuXG5cdHJldHVybiBuZXcgUHJvbWlzZSgocmVzb2x2ZSwgcmVqZWN0KSA9PiB7XG5cdFx0aWYgKHNpZ25hbC5hYm9ydGVkKSB7XG5cdFx0XHRyZWplY3Qoc2lnbmFsLnJlYXNvbik7XG5cdFx0fVxuXHRcdHNpZ25hbC5hZGRFdmVudExpc3RlbmVyKFwiYWJvcnRcIiwgKCkgPT4ge1xuXHRcdFx0bW9kZWwub2ZmKFwibXNnOmN1c3RvbVwiLCBoYW5kbGVyKTtcblx0XHRcdHJlamVjdChzaWduYWwucmVhc29uKTtcblx0XHR9KTtcblxuXHRcdC8qKlxuXHRcdCAqIEBwYXJhbSB7eyBpZDogc3RyaW5nLCBraW5kOiBcImFueXdpZGdldC1jb21tYW5kLXJlc3BvbnNlXCIsIHJlc3BvbnNlOiBUIH19IG1zZ1xuXHRcdCAqIEBwYXJhbSB7RGF0YVZpZXdbXX0gYnVmZmVyc1xuXHRcdCAqL1xuXHRcdGZ1bmN0aW9uIGhhbmRsZXIobXNnLCBidWZmZXJzKSB7XG5cdFx0XHRpZiAoIShtc2cuaWQgPT09IGlkKSkgcmV0dXJuO1xuXHRcdFx0cmVzb2x2ZShbbXNnLnJlc3BvbnNlLCBidWZmZXJzXSk7XG5cdFx0XHRtb2RlbC5vZmYoXCJtc2c6Y3VzdG9tXCIsIGhhbmRsZXIpO1xuXHRcdH1cblx0XHRtb2RlbC5vbihcIm1zZzpjdXN0b21cIiwgaGFuZGxlcik7XG5cdFx0bW9kZWwuc2VuZChcblx0XHRcdHsgaWQsIGtpbmQ6IFwiYW55d2lkZ2V0LWNvbW1hbmRcIiwgbmFtZSwgbXNnIH0sXG5cdFx0XHR1bmRlZmluZWQsXG5cdFx0XHRvcHRpb25zLmJ1ZmZlcnMgPz8gW10sXG5cdFx0KTtcblx0fSk7XG59XG5cbi8qKlxuICogUG9seWZpbGwgZm9yIHtAbGluayBodHRwczovL2RldmVsb3Blci5tb3ppbGxhLm9yZy9lbi1VUy9kb2NzL1dlYi9KYXZhU2NyaXB0L1JlZmVyZW5jZS9HbG9iYWxfT2JqZWN0cy9Qcm9taXNlL3dpdGhSZXNvbHZlcnMgUHJvbWlzZS53aXRoUmVzb2x2ZXJzfVxuICpcbiAqIFRyZXZvcigyMDI1LTAzLTE0KTogU2hvdWxkIGJlIGFibGUgdG8gcmVtb3ZlIG9uY2UgbW9yZSBzdGFibGUgYWNyb3NzIGJyb3dzZXJzLlxuICpcbiAqIEB0ZW1wbGF0ZSBUXG4gKiBAcmV0dXJucyB7UHJvbWlzZVdpdGhSZXNvbHZlcnM8VD59XG4gKi9cbmZ1bmN0aW9uIHByb21pc2Vfd2l0aF9yZXNvbHZlcnMoKSB7XG5cdGxldCByZXNvbHZlO1xuXHRsZXQgcmVqZWN0O1xuXHRsZXQgcHJvbWlzZSA9IG5ldyBQcm9taXNlKChyZXMsIHJlaikgPT4ge1xuXHRcdHJlc29sdmUgPSByZXM7XG5cdFx0cmVqZWN0ID0gcmVqO1xuXHR9KTtcblx0Ly8gQHRzLWV4cGVjdC1lcnJvciAtIFdlIGtub3cgdGhlc2UgdHlwZXMgYXJlIG9rXG5cdHJldHVybiB7IHByb21pc2UsIHJlc29sdmUsIHJlamVjdCB9O1xufVxuXG4vKipcbiAqIEB0ZW1wbGF0ZSB7UmVjb3JkPHN0cmluZywgdW5rbm93bj59IFRcbiAqIEB0ZW1wbGF0ZSB7a2V5b2YgVCAmIHN0cmluZ30gS1xuICogQHBhcmFtIHtBbnlNb2RlbDxUPn0gbW9kZWxcbiAqIEBwYXJhbSB7S30gbmFtZVxuICogQHBhcmFtIHt7IHNpZ25hbD86IEFib3J0U2lnbmFsfX0gb3B0aW9uc1xuICogQHJldHVybnMge3NvbGlkLkFjY2Vzc29yPFRbS10+fVxuICovXG5mdW5jdGlvbiBvYnNlcnZlKG1vZGVsLCBuYW1lLCB7IHNpZ25hbCB9KSB7XG5cdGxldCBbZ2V0LCBzZXRdID0gc29saWQuY3JlYXRlU2lnbmFsKG1vZGVsLmdldChuYW1lKSk7XG5cdGxldCB1cGRhdGUgPSAoKSA9PiBzZXQoKCkgPT4gbW9kZWwuZ2V0KG5hbWUpKTtcblx0bW9kZWwub24oYGNoYW5nZToke25hbWV9YCwgdXBkYXRlKTtcblx0c2lnbmFsPy5hZGRFdmVudExpc3RlbmVyKFwiYWJvcnRcIiwgKCkgPT4ge1xuXHRcdG1vZGVsLm9mZihgY2hhbmdlOiR7bmFtZX1gLCB1cGRhdGUpO1xuXHR9KTtcblx0cmV0dXJuIGdldDtcbn1cblxuLyoqXG4gKiBAdHlwZWRlZiBTdGF0ZVxuICogQHByb3BlcnR5IHtzdHJpbmd9IF9lc21cbiAqIEBwcm9wZXJ0eSB7c3RyaW5nfSBfYW55d2lkZ2V0X2lkXG4gKiBAcHJvcGVydHkge3N0cmluZyB8IHVuZGVmaW5lZH0gX2Nzc1xuICovXG5cbmNsYXNzIFJ1bnRpbWUge1xuXHQvKiogQHR5cGUge3NvbGlkLkFjY2Vzc29yPFJlc3VsdDxBbnlXaWRnZXQ+Pn0gKi9cblx0Ly8gQHRzLWV4cGVjdC1lcnJvciAtIFNldCBzeW5jaHJvbm91c2x5IGluIGNvbnN0cnVjdG9yLlxuXHQjd2lkZ2V0X3Jlc3VsdDtcblx0LyoqIEB0eXBlIHtBYm9ydFNpZ25hbH0gKi9cblx0I3NpZ25hbDtcblx0LyoqIEB0eXBlIHtQcm9taXNlPHZvaWQ+fSAqL1xuXHRyZWFkeTtcblxuXHQvKipcblx0ICogQHBhcmFtIHtiYXNlLkRPTVdpZGdldE1vZGVsfSBtb2RlbFxuXHQgKiBAcGFyYW0ge3sgc2lnbmFsOiBBYm9ydFNpZ25hbCB9fSBvcHRpb25zXG5cdCAqL1xuXHRjb25zdHJ1Y3Rvcihtb2RlbCwgb3B0aW9ucykge1xuXHRcdC8qKiBAdHlwZSB7UHJvbWlzZVdpdGhSZXNvbHZlcnM8dm9pZD59ICovXG5cdFx0bGV0IHJlc29sdmVycyA9IHByb21pc2Vfd2l0aF9yZXNvbHZlcnMoKTtcblx0XHR0aGlzLnJlYWR5ID0gcmVzb2x2ZXJzLnByb21pc2U7XG5cdFx0dGhpcy4jc2lnbmFsID0gb3B0aW9ucy5zaWduYWw7XG5cdFx0dGhpcy4jc2lnbmFsLnRocm93SWZBYm9ydGVkKCk7XG5cdFx0dGhpcy4jc2lnbmFsLmFkZEV2ZW50TGlzdGVuZXIoXCJhYm9ydFwiLCAoKSA9PiBkaXNwb3NlKCkpO1xuXHRcdEFib3J0U2lnbmFsLnRpbWVvdXQoMjAwMCkuYWRkRXZlbnRMaXN0ZW5lcihcImFib3J0XCIsICgpID0+IHtcblx0XHRcdHJlc29sdmVycy5yZWplY3QobmV3IEVycm9yKFwiW2FueXdpZGdldF0gRmFpbGVkIHRvIGluaXRpYWxpemUgbW9kZWwuXCIpKTtcblx0XHR9KTtcblx0XHRsZXQgZGlzcG9zZSA9IHNvbGlkLmNyZWF0ZVJvb3QoKGRpc3Bvc2UpID0+IHtcblx0XHRcdC8qKiBAdHlwZSB7QW55TW9kZWw8U3RhdGU+fSAqL1xuXHRcdFx0Ly8gQHRzLWV4cGVjdC1lcnJvciAtIFR5cGVzIGRvbid0IHN1ZmZpY2llbnRseSBvdmVybGFwLCBzbyB3ZSBjYXN0IGhlcmUgZm9yIHR5cGUtc2FmZSBhY2Nlc3Ncblx0XHRcdGxldCB0eXBlZF9tb2RlbCA9IG1vZGVsO1xuXHRcdFx0bGV0IGlkID0gdHlwZWRfbW9kZWwuZ2V0KFwiX2FueXdpZGdldF9pZFwiKTtcblx0XHRcdGxldCBjc3MgPSBvYnNlcnZlKHR5cGVkX21vZGVsLCBcIl9jc3NcIiwgeyBzaWduYWw6IHRoaXMuI3NpZ25hbCB9KTtcblx0XHRcdGxldCBlc20gPSBvYnNlcnZlKHR5cGVkX21vZGVsLCBcIl9lc21cIiwgeyBzaWduYWw6IHRoaXMuI3NpZ25hbCB9KTtcblx0XHRcdGxldCBbd2lkZ2V0X3Jlc3VsdCwgc2V0X3dpZGdldF9yZXN1bHRdID0gc29saWQuY3JlYXRlU2lnbmFsKFxuXHRcdFx0XHQvKiogQHR5cGUge1Jlc3VsdDxBbnlXaWRnZXQ+fSAqLyAoeyBzdGF0dXM6IFwicGVuZGluZ1wiIH0pLFxuXHRcdFx0KTtcblx0XHRcdHRoaXMuI3dpZGdldF9yZXN1bHQgPSB3aWRnZXRfcmVzdWx0O1xuXG5cdFx0XHRzb2xpZC5jcmVhdGVFZmZlY3QoXG5cdFx0XHRcdHNvbGlkLm9uKFxuXHRcdFx0XHRcdGNzcyxcblx0XHRcdFx0XHQoKSA9PiBjb25zb2xlLmRlYnVnKGBbYW55d2lkZ2V0XSBjc3MgaG90IHVwZGF0ZWQ6ICR7aWR9YCksXG5cdFx0XHRcdFx0eyBkZWZlcjogdHJ1ZSB9LFxuXHRcdFx0XHQpLFxuXHRcdFx0KTtcblx0XHRcdHNvbGlkLmNyZWF0ZUVmZmVjdChcblx0XHRcdFx0c29saWQub24oXG5cdFx0XHRcdFx0ZXNtLFxuXHRcdFx0XHRcdCgpID0+IGNvbnNvbGUuZGVidWcoYFthbnl3aWRnZXRdIGVzbSBob3QgdXBkYXRlZDogJHtpZH1gKSxcblx0XHRcdFx0XHR7IGRlZmVyOiB0cnVlIH0sXG5cdFx0XHRcdCksXG5cdFx0XHQpO1xuXHRcdFx0c29saWQuY3JlYXRlRWZmZWN0KCgpID0+IHtcblx0XHRcdFx0bG9hZF9jc3MoY3NzKCksIGlkKTtcblx0XHRcdH0pO1xuXHRcdFx0c29saWQuY3JlYXRlRWZmZWN0KCgpID0+IHtcblx0XHRcdFx0bGV0IGNvbnRyb2xsZXIgPSBuZXcgQWJvcnRDb250cm9sbGVyKCk7XG5cdFx0XHRcdHNvbGlkLm9uQ2xlYW51cCgoKSA9PiBjb250cm9sbGVyLmFib3J0KCkpO1xuXHRcdFx0XHRtb2RlbC5vZmYobnVsbCwgbnVsbCwgSU5JVElBTElaRV9NQVJLRVIpO1xuXHRcdFx0XHRsb2FkX3dpZGdldChlc20oKSwgaWQpXG5cdFx0XHRcdFx0LnRoZW4oYXN5bmMgKHdpZGdldCkgPT4ge1xuXHRcdFx0XHRcdFx0aWYgKGNvbnRyb2xsZXIuc2lnbmFsLmFib3J0ZWQpIHtcblx0XHRcdFx0XHRcdFx0cmV0dXJuO1xuXHRcdFx0XHRcdFx0fVxuXHRcdFx0XHRcdFx0bGV0IGNsZWFudXAgPSBhd2FpdCB3aWRnZXQuaW5pdGlhbGl6ZT8uKHtcblx0XHRcdFx0XHRcdFx0bW9kZWw6IG1vZGVsX3Byb3h5KG1vZGVsLCBJTklUSUFMSVpFX01BUktFUiksXG5cdFx0XHRcdFx0XHRcdGV4cGVyaW1lbnRhbDoge1xuXHRcdFx0XHRcdFx0XHRcdC8vIEB0cy1leHBlY3QtZXJyb3IgLSBiaW5kIGlzbid0IHdvcmtpbmdcblx0XHRcdFx0XHRcdFx0XHRpbnZva2U6IGludm9rZS5iaW5kKG51bGwsIG1vZGVsKSxcblx0XHRcdFx0XHRcdFx0fSxcblx0XHRcdFx0XHRcdH0pO1xuXHRcdFx0XHRcdFx0aWYgKGNvbnRyb2xsZXIuc2lnbmFsLmFib3J0ZWQpIHtcblx0XHRcdFx0XHRcdFx0c2FmZV9jbGVhbnVwKGNsZWFudXAsIFwiZXNtIHVwZGF0ZVwiKTtcblx0XHRcdFx0XHRcdFx0cmV0dXJuO1xuXHRcdFx0XHRcdFx0fVxuXHRcdFx0XHRcdFx0Y29udHJvbGxlci5zaWduYWwuYWRkRXZlbnRMaXN0ZW5lcihcImFib3J0XCIsICgpID0+XG5cdFx0XHRcdFx0XHRcdHNhZmVfY2xlYW51cChjbGVhbnVwLCBcImVzbSB1cGRhdGVcIiksXG5cdFx0XHRcdFx0XHQpO1xuXHRcdFx0XHRcdFx0c2V0X3dpZGdldF9yZXN1bHQoeyBzdGF0dXM6IFwicmVhZHlcIiwgZGF0YTogd2lkZ2V0IH0pO1xuXHRcdFx0XHRcdFx0cmVzb2x2ZXJzLnJlc29sdmUoKTtcblx0XHRcdFx0XHR9KVxuXHRcdFx0XHRcdC5jYXRjaCgoZXJyb3IpID0+IHNldF93aWRnZXRfcmVzdWx0KHsgc3RhdHVzOiBcImVycm9yXCIsIGVycm9yIH0pKTtcblx0XHRcdH0pO1xuXG5cdFx0XHRyZXR1cm4gZGlzcG9zZTtcblx0XHR9KTtcblx0fVxuXG5cdC8qKlxuXHQgKiBAcGFyYW0ge2Jhc2UuRE9NV2lkZ2V0Vmlld30gdmlld1xuXHQgKiBAcGFyYW0ge3sgc2lnbmFsOiBBYm9ydFNpZ25hbCB9fSBvcHRpb25zXG5cdCAqIEByZXR1cm5zIHtQcm9taXNlPHZvaWQ+fVxuXHQgKi9cblx0YXN5bmMgY3JlYXRlX3ZpZXcodmlldywgb3B0aW9ucykge1xuXHRcdGxldCBtb2RlbCA9IHZpZXcubW9kZWw7XG5cdFx0bGV0IHNpZ25hbCA9IEFib3J0U2lnbmFsLmFueShbdGhpcy4jc2lnbmFsLCBvcHRpb25zLnNpZ25hbF0pOyAvLyBlaXRoZXIgbW9kZWwgb3IgdmlldyBkZXN0cm95ZWRcblx0XHRzaWduYWwudGhyb3dJZkFib3J0ZWQoKTtcblx0XHRzaWduYWwuYWRkRXZlbnRMaXN0ZW5lcihcImFib3J0XCIsICgpID0+IGRpc3Bvc2UoKSk7XG5cdFx0bGV0IGRpc3Bvc2UgPSBzb2xpZC5jcmVhdGVSb290KChkaXNwb3NlKSA9PiB7XG5cdFx0XHRzb2xpZC5jcmVhdGVFZmZlY3QoKCkgPT4ge1xuXHRcdFx0XHQvLyBDbGVhciBhbGwgcHJldmlvdXMgZXZlbnQgbGlzdGVuZXJzIGZyb20gdGhpcyBob29rLlxuXHRcdFx0XHRtb2RlbC5vZmYobnVsbCwgbnVsbCwgdmlldyk7XG5cdFx0XHRcdHZpZXcuJGVsLmVtcHR5KCk7XG5cdFx0XHRcdGxldCByZXN1bHQgPSB0aGlzLiN3aWRnZXRfcmVzdWx0KCk7XG5cdFx0XHRcdGlmIChyZXN1bHQuc3RhdHVzID09PSBcInBlbmRpbmdcIikge1xuXHRcdFx0XHRcdHJldHVybjtcblx0XHRcdFx0fVxuXHRcdFx0XHRpZiAocmVzdWx0LnN0YXR1cyA9PT0gXCJlcnJvclwiKSB7XG5cdFx0XHRcdFx0dGhyb3dfYW55d2lkZ2V0X2Vycm9yKHJlc3VsdC5lcnJvcik7XG5cdFx0XHRcdFx0cmV0dXJuO1xuXHRcdFx0XHR9XG5cdFx0XHRcdGxldCBjb250cm9sbGVyID0gbmV3IEFib3J0Q29udHJvbGxlcigpO1xuXHRcdFx0XHRzb2xpZC5vbkNsZWFudXAoKCkgPT4gY29udHJvbGxlci5hYm9ydCgpKTtcblx0XHRcdFx0UHJvbWlzZS5yZXNvbHZlKClcblx0XHRcdFx0XHQudGhlbihhc3luYyAoKSA9PiB7XG5cdFx0XHRcdFx0XHRsZXQgY2xlYW51cCA9IGF3YWl0IHJlc3VsdC5kYXRhLnJlbmRlcj8uKHtcblx0XHRcdFx0XHRcdFx0bW9kZWw6IG1vZGVsX3Byb3h5KG1vZGVsLCB2aWV3KSxcblx0XHRcdFx0XHRcdFx0ZWw6IHZpZXcuZWwsXG5cdFx0XHRcdFx0XHRcdGV4cGVyaW1lbnRhbDoge1xuXHRcdFx0XHRcdFx0XHRcdC8vIEB0cy1leHBlY3QtZXJyb3IgLSBiaW5kIGlzbid0IHdvcmtpbmdcblx0XHRcdFx0XHRcdFx0XHRpbnZva2U6IGludm9rZS5iaW5kKG51bGwsIG1vZGVsKSxcblx0XHRcdFx0XHRcdFx0fSxcblx0XHRcdFx0XHRcdH0pO1xuXHRcdFx0XHRcdFx0aWYgKGNvbnRyb2xsZXIuc2lnbmFsLmFib3J0ZWQpIHtcblx0XHRcdFx0XHRcdFx0c2FmZV9jbGVhbnVwKGNsZWFudXAsIFwiZGlzcG9zZSB2aWV3IC0gYWxyZWFkeSBhYm9ydGVkXCIpO1xuXHRcdFx0XHRcdFx0XHRyZXR1cm47XG5cdFx0XHRcdFx0XHR9XG5cdFx0XHRcdFx0XHRjb250cm9sbGVyLnNpZ25hbC5hZGRFdmVudExpc3RlbmVyKFwiYWJvcnRcIiwgKCkgPT5cblx0XHRcdFx0XHRcdFx0c2FmZV9jbGVhbnVwKGNsZWFudXAsIFwiZGlzcG9zZSB2aWV3IC0gYWJvcnRlZFwiKSxcblx0XHRcdFx0XHRcdCk7XG5cdFx0XHRcdFx0fSlcblx0XHRcdFx0XHQuY2F0Y2goKGVycm9yKSA9PiB0aHJvd19hbnl3aWRnZXRfZXJyb3IoZXJyb3IpKTtcblx0XHRcdH0pO1xuXHRcdFx0cmV0dXJuICgpID0+IGRpc3Bvc2UoKTtcblx0XHR9KTtcblx0fVxufVxuXG4vLyBAdHMtZXhwZWN0LWVycm9yIC0gaW5qZWN0ZWQgYnkgYnVuZGxlclxubGV0IHZlcnNpb24gPSBnbG9iYWxUaGlzLlZFUlNJT047XG5cbi8qKlxuICogQHBhcmFtIHtiYXNlfSBvcHRpb25zXG4gKiBAcmV0dXJucyB7eyBBbnlNb2RlbDogdHlwZW9mIGJhc2UuRE9NV2lkZ2V0TW9kZWwsIEFueVZpZXc6IHR5cGVvZiBiYXNlLkRPTVdpZGdldFZpZXcgfX1cbiAqL1xuZXhwb3J0IGRlZmF1bHQgZnVuY3Rpb24gKHsgRE9NV2lkZ2V0TW9kZWwsIERPTVdpZGdldFZpZXcgfSkge1xuXHQvKiogQHR5cGUge1dlYWtNYXA8QW55TW9kZWwsIFJ1bnRpbWU+fSAqL1xuXHRsZXQgUlVOVElNRVMgPSBuZXcgV2Vha01hcCgpO1xuXG5cdGNsYXNzIEFueU1vZGVsIGV4dGVuZHMgRE9NV2lkZ2V0TW9kZWwge1xuXHRcdHN0YXRpYyBtb2RlbF9uYW1lID0gXCJBbnlNb2RlbFwiO1xuXHRcdHN0YXRpYyBtb2RlbF9tb2R1bGUgPSBcImFueXdpZGdldFwiO1xuXHRcdHN0YXRpYyBtb2RlbF9tb2R1bGVfdmVyc2lvbiA9IHZlcnNpb247XG5cblx0XHRzdGF0aWMgdmlld19uYW1lID0gXCJBbnlWaWV3XCI7XG5cdFx0c3RhdGljIHZpZXdfbW9kdWxlID0gXCJhbnl3aWRnZXRcIjtcblx0XHRzdGF0aWMgdmlld19tb2R1bGVfdmVyc2lvbiA9IHZlcnNpb247XG5cblx0XHQvKiogQHBhcmFtIHtQYXJhbWV0ZXJzPEluc3RhbmNlVHlwZTxET01XaWRnZXRNb2RlbD5bXCJpbml0aWFsaXplXCJdPn0gYXJncyAqL1xuXHRcdGluaXRpYWxpemUoLi4uYXJncykge1xuXHRcdFx0c3VwZXIuaW5pdGlhbGl6ZSguLi5hcmdzKTtcblx0XHRcdGxldCBjb250cm9sbGVyID0gbmV3IEFib3J0Q29udHJvbGxlcigpO1xuXHRcdFx0dGhpcy5vbmNlKFwiZGVzdHJveVwiLCAoKSA9PiB7XG5cdFx0XHRcdGNvbnRyb2xsZXIuYWJvcnQoXCJbYW55d2lkZ2V0XSBSdW50aW1lIGRlc3Ryb3llZC5cIik7XG5cdFx0XHRcdFJVTlRJTUVTLmRlbGV0ZSh0aGlzKTtcblx0XHRcdH0pO1xuXHRcdFx0UlVOVElNRVMuc2V0KHRoaXMsIG5ldyBSdW50aW1lKHRoaXMsIHsgc2lnbmFsOiBjb250cm9sbGVyLnNpZ25hbCB9KSk7XG5cdFx0fVxuXG5cdFx0LyoqIEBwYXJhbSB7UGFyYW1ldGVyczxJbnN0YW5jZVR5cGU8RE9NV2lkZ2V0TW9kZWw+W1wiX2hhbmRsZV9jb21tX21zZ1wiXT59IG1zZyAqL1xuXHRcdGFzeW5jIF9oYW5kbGVfY29tbV9tc2coLi4ubXNnKSB7XG5cdFx0XHRsZXQgcnVudGltZSA9IFJVTlRJTUVTLmdldCh0aGlzKTtcblx0XHRcdGF3YWl0IHJ1bnRpbWU/LnJlYWR5O1xuXHRcdFx0cmV0dXJuIHN1cGVyLl9oYW5kbGVfY29tbV9tc2coLi4ubXNnKTtcblx0XHR9XG5cblx0XHQvKipcblx0XHQgKiBAcGFyYW0ge1JlY29yZDxzdHJpbmcsIGFueT59IHN0YXRlXG5cdFx0ICpcblx0XHQgKiBXZSBvdmVycmlkZSB0byBzdXBwb3J0IGJpbmFyeSB0cmFpbGV0cyBiZWNhdXNlIEpTT04ucGFyc2UoSlNPTi5zdHJpbmdpZnkoKSlcblx0XHQgKiBkb2VzIG5vdCBwcm9wZXJseSBjbG9uZSBiaW5hcnkgZGF0YSAoaXQganVzdCByZXR1cm5zIGFuIGVtcHR5IG9iamVjdCkuXG5cdFx0ICpcblx0XHQgKiBodHRwczovL2dpdGh1Yi5jb20vanVweXRlci13aWRnZXRzL2lweXdpZGdldHMvYmxvYi80NzA1OGEzNzNkMmMyYjNhY2YxMDE2NzdiMjc0NWUxNGI3NmRkNzRiL3BhY2thZ2VzL2Jhc2Uvc3JjL3dpZGdldC50cyNMNTYyLUw1ODNcblx0XHQgKi9cblx0XHRzZXJpYWxpemUoc3RhdGUpIHtcblx0XHRcdGxldCBzZXJpYWxpemVycyA9XG5cdFx0XHRcdC8qKiBAdHlwZSB7RE9NV2lkZ2V0TW9kZWx9ICovICh0aGlzLmNvbnN0cnVjdG9yKS5zZXJpYWxpemVycyB8fCB7fTtcblx0XHRcdGZvciAobGV0IGsgb2YgT2JqZWN0LmtleXMoc3RhdGUpKSB7XG5cdFx0XHRcdHRyeSB7XG5cdFx0XHRcdFx0bGV0IHNlcmlhbGl6ZSA9IHNlcmlhbGl6ZXJzW2tdPy5zZXJpYWxpemU7XG5cdFx0XHRcdFx0aWYgKHNlcmlhbGl6ZSkge1xuXHRcdFx0XHRcdFx0c3RhdGVba10gPSBzZXJpYWxpemUoc3RhdGVba10sIHRoaXMpO1xuXHRcdFx0XHRcdH0gZWxzZSBpZiAoayA9PT0gXCJsYXlvdXRcIiB8fCBrID09PSBcInN0eWxlXCIpIHtcblx0XHRcdFx0XHRcdC8vIFRoZXNlIGtleXMgY29tZSBmcm9tIGlweXdpZGdldHMsIHJlbHkgb24gSlNPTi5zdHJpbmdpZnkgdHJpY2suXG5cdFx0XHRcdFx0XHRzdGF0ZVtrXSA9IEpTT04ucGFyc2UoSlNPTi5zdHJpbmdpZnkoc3RhdGVba10pKTtcblx0XHRcdFx0XHR9IGVsc2Uge1xuXHRcdFx0XHRcdFx0c3RhdGVba10gPSBzdHJ1Y3R1cmVkQ2xvbmUoc3RhdGVba10pO1xuXHRcdFx0XHRcdH1cblx0XHRcdFx0XHRpZiAodHlwZW9mIHN0YXRlW2tdPy50b0pTT04gPT09IFwiZnVuY3Rpb25cIikge1xuXHRcdFx0XHRcdFx0c3RhdGVba10gPSBzdGF0ZVtrXS50b0pTT04oKTtcblx0XHRcdFx0XHR9XG5cdFx0XHRcdH0gY2F0Y2ggKGUpIHtcblx0XHRcdFx0XHRjb25zb2xlLmVycm9yKFwiRXJyb3Igc2VyaWFsaXppbmcgd2lkZ2V0IHN0YXRlIGF0dHJpYnV0ZTogXCIsIGspO1xuXHRcdFx0XHRcdHRocm93IGU7XG5cdFx0XHRcdH1cblx0XHRcdH1cblx0XHRcdHJldHVybiBzdGF0ZTtcblx0XHR9XG5cdH1cblxuXHRjbGFzcyBBbnlWaWV3IGV4dGVuZHMgRE9NV2lkZ2V0VmlldyB7XG5cdFx0I2NvbnRyb2xsZXIgPSBuZXcgQWJvcnRDb250cm9sbGVyKCk7XG5cdFx0YXN5bmMgcmVuZGVyKCkge1xuXHRcdFx0bGV0IHJ1bnRpbWUgPSBSVU5USU1FUy5nZXQodGhpcy5tb2RlbCk7XG5cdFx0XHRhc3NlcnQocnVudGltZSwgXCJbYW55d2lkZ2V0XSBSdW50aW1lIG5vdCBmb3VuZC5cIik7XG5cdFx0XHRhd2FpdCBydW50aW1lLmNyZWF0ZV92aWV3KHRoaXMsIHsgc2lnbmFsOiB0aGlzLiNjb250cm9sbGVyLnNpZ25hbCB9KTtcblx0XHR9XG5cdFx0cmVtb3ZlKCkge1xuXHRcdFx0dGhpcy4jY29udHJvbGxlci5hYm9ydChcIlthbnl3aWRnZXRdIFZpZXcgZGVzdHJveWVkLlwiKTtcblx0XHRcdHN1cGVyLnJlbW92ZSgpO1xuXHRcdH1cblx0fVxuXG5cdHJldHVybiB7IEFueU1vZGVsLCBBbnlWaWV3IH07XG59XG4iLCJpbXBvcnQgKiBhcyBiYXNlIGZyb20gXCJAanVweXRlci13aWRnZXRzL2Jhc2VcIjtcbmltcG9ydCBjcmVhdGUgZnJvbSBcIi4vd2lkZ2V0LmpzXCI7XG5cbi8qKlxuICogQHR5cGVkZWYgSnVweXRlckxhYlJlZ2lzdHJ5XG4gKiBAcHJvcGVydHkgeyh3aWRnZXQ6IHsgbmFtZTogc3RyaW5nLCB2ZXJzaW9uOiBzdHJpbmcsIGV4cG9ydHM6IGFueSB9KSA9PiB2b2lkfSByZWdpc3RlcldpZGdldFxuICovXG5cbmV4cG9ydCBkZWZhdWx0IHtcblx0aWQ6IFwiYW55d2lkZ2V0OnBsdWdpblwiLFxuXHRyZXF1aXJlczogWy8qKiBAdHlwZXt1bmtub3dufSAqLyAoYmFzZS5JSnVweXRlcldpZGdldFJlZ2lzdHJ5KV0sXG5cdGFjdGl2YXRlOiAoXG5cdFx0LyoqIEB0eXBlIHt1bmtub3dufSAqLyBfYXBwLFxuXHRcdC8qKiBAdHlwZSB7SnVweXRlckxhYlJlZ2lzdHJ5fSAqLyByZWdpc3RyeSxcblx0KSA9PiB7XG5cdFx0bGV0IGV4cG9ydHMgPSBjcmVhdGUoYmFzZSk7XG5cdFx0cmVnaXN0cnkucmVnaXN0ZXJXaWRnZXQoe1xuXHRcdFx0bmFtZTogXCJhbnl3aWRnZXRcIixcblx0XHRcdC8vIEB0cy1leHBlY3QtZXJyb3IgQWRkZWQgYnkgYnVuZGxlclxuXHRcdFx0dmVyc2lvbjogZ2xvYmFsVGhpcy5WRVJTSU9OLFxuXHRcdFx0ZXhwb3J0cyxcblx0XHR9KTtcblx0fSxcblx0YXV0b1N0YXJ0OiB0cnVlLFxufTtcbiJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQXFDO0FBQ0g7O0FBRWxDO0FBQ0EsY0FBYywrQkFBK0I7O0FBRTdDO0FBQ0E7QUFDQSxhQUFhLG9CQUFvQjtBQUNqQzs7QUFFQTtBQUNBO0FBQ0EscUJBQXFCO0FBQ3JCLGlCQUFpQjtBQUNqQjs7QUFFQTtBQUNBO0FBQ0Esa0JBQWtCO0FBQ2xCLG1CQUFtQjtBQUNuQjs7QUFFQTtBQUNBLFdBQVcsU0FBUztBQUNwQixXQUFXLFFBQVE7QUFDbkIsYUFBYTtBQUNiO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0EsV0FBVyxRQUFRO0FBQ25CLGFBQWEsa0JBQWtCLE9BQU8sY0FBYyxPQUFPO0FBQzNEO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0EsV0FBVyxRQUFRO0FBQ25CLFdBQVcsUUFBUTtBQUNuQixhQUFhO0FBQ2I7QUFDQTtBQUNBLFlBQVksd0JBQXdCO0FBQ3BDLCtDQUErQyxhQUFhOztBQUU1RDtBQUNBO0FBQ0E7QUFDQTtBQUNBLDJCQUEyQixpQkFBaUI7QUFDNUM7QUFDQTtBQUNBO0FBQ0E7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